"""BI 分析 API"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError
from sqlalchemy import and_, func, literal, select, union
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import ColumnElement

from app import db
from app.cache import check_bi_rate_limit, get_bi_cache, set_bi_cache
from app.models import CostEntry, RevenueEntry, Sheep
from app.schemas import (
    CohortAnalysisRequest,
    CohortFilterModel,
    CostBenefitRequest,
    TimeRangeModel,
    create_error_response,
)

bp = Blueprint('bi', __name__)

_DIMENSION_CONFIG = {
    'breed': {
        'sheep_attr': 'Breed',
        'finance_attr': 'breed',
        'fallback': '未填寫',
    },
    'lactation_number': {
        'sheep_attr': 'Lactation',
        'finance_attr': 'lactation_number',
        'fallback': -1,
    },
    'production_stage': {
        'sheep_attr': 'status',
        'finance_attr': 'production_stage',
        'fallback': '未填寫',
    },
}


def _dimension_expression(
    model: type[Sheep] | type[CostEntry] | type[RevenueEntry],
    dimension: str,
) -> ColumnElement[Any]:
    config = _DIMENSION_CONFIG[dimension]
    column = getattr(model, config['sheep_attr'] if model is Sheep else config['finance_attr'])
    fallback = config['fallback']
    return func.coalesce(column, literal(fallback))


def _apply_sheep_filters(query: Select, filters: CohortFilterModel | None) -> Select:
    if not filters:
        return query
    if filters.breed:
        query = query.where(Sheep.Breed.in_(filters.breed))
    if filters.lactation_number:
        query = query.where(Sheep.Lactation.in_(filters.lactation_number))
    if filters.production_stage:
        query = query.where(Sheep.status.in_(filters.production_stage))
    if filters.min_age_months is not None:
        query = query.where(Sheep.Age_Months >= filters.min_age_months)
    if filters.max_age_months is not None:
        query = query.where(Sheep.Age_Months <= filters.max_age_months)
    return query


def _apply_finance_filters(
    query: Select,
    model: type[CostEntry] | type[RevenueEntry],
    filters: CohortFilterModel | None,
    time_range: TimeRangeModel | None,
) -> Select:
    conditions = [model.user_id == current_user.id]

    if filters:
        if filters.category:
            conditions.append(model.category.in_(filters.category))
        if filters.breed:
            conditions.append(model.breed.in_(filters.breed))
        if filters.lactation_number:
            conditions.append(model.lactation_number.in_(filters.lactation_number))
        if filters.production_stage:
            conditions.append(model.production_stage.in_(filters.production_stage))
        if filters.min_age_months is not None:
            conditions.append(model.age_months >= filters.min_age_months)
        if filters.max_age_months is not None:
            conditions.append(model.age_months <= filters.max_age_months)

    if time_range:
        if time_range.start:
            conditions.append(model.recorded_at >= time_range.start)
        if time_range.end:
            conditions.append(model.recorded_at <= time_range.end)

    return query.where(and_(*conditions))


def _serialize_decimal(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _cohort_analysis(payload: dict) -> dict:
    try:
        request_model = CohortAnalysisRequest(**payload)
    except ValidationError as exc:
        return {'error': create_error_response('請求資料驗證失敗', exc.errors()), 'status': 400}

    wrapped_payload = {'endpoint': 'cohort', 'payload': request_model.model_dump()}
    cached = get_bi_cache(current_user.id, wrapped_payload)
    if cached:
        return {'data': cached, 'status': 200}

    if not check_bi_rate_limit(current_user.id, 'cohort-analysis'):
        return {'error': create_error_response('查詢次數過多，請稍後再試'), 'status': 429}

    dimension_exprs = []
    dimension_labels = []
    for dimension in request_model.cohort_by:
        expr = _dimension_expression(Sheep, dimension).label(dimension)
        dimension_exprs.append(expr)
        dimension_labels.append(dimension)

    sheep_query = select(
        *dimension_exprs,
        func.count(Sheep.id).label('sheep_count'),
        func.avg(Sheep.Body_Weight_kg).label('avg_weight'),
        func.avg(Sheep.milk_yield_kg_day).label('avg_milk'),
    ).where(Sheep.user_id == current_user.id)
    sheep_query = _apply_sheep_filters(sheep_query, request_model.filters)
    if dimension_exprs:
        sheep_query = sheep_query.group_by(*dimension_exprs)
    sheep_subquery = sheep_query.subquery('sheep_cohort')

    cost_group_exprs = [
        _dimension_expression(CostEntry, dimension).label(dimension) for dimension in request_model.cohort_by
    ]
    cost_query = select(
        *cost_group_exprs,
        func.sum(CostEntry.amount).label('total_cost'),
    )
    cost_query = _apply_finance_filters(cost_query, CostEntry, request_model.filters, request_model.time_range)
    if cost_group_exprs:
        cost_query = cost_query.group_by(*cost_group_exprs)
    cost_subquery = cost_query.subquery('cost_cohort')

    revenue_group_exprs = [
        _dimension_expression(RevenueEntry, dimension).label(dimension) for dimension in request_model.cohort_by
    ]
    revenue_query = select(
        *revenue_group_exprs,
        func.sum(RevenueEntry.amount).label('total_revenue'),
    )
    revenue_query = _apply_finance_filters(revenue_query, RevenueEntry, request_model.filters, request_model.time_range)
    if revenue_group_exprs:
        revenue_query = revenue_query.group_by(*revenue_group_exprs)
    revenue_subquery = revenue_query.subquery('revenue_cohort')

    group_selects = [
        select(*[subquery.c[label] for label in dimension_labels]).select_from(subquery)
        for subquery in (sheep_subquery, cost_subquery, revenue_subquery)
    ]

    # 移除可能的重複群組並確保包含沒有對應羊隻資料的財務紀錄
    groups_query = union(*group_selects)
    groups_subquery = groups_query.subquery('cohort_groups')

    join_condition_sheep = and_(
        *[groups_subquery.c[label] == sheep_subquery.c[label] for label in dimension_labels]
    )
    join_condition_cost = and_(*[groups_subquery.c[label] == cost_subquery.c[label] for label in dimension_labels])
    join_condition_revenue = and_(
        *[groups_subquery.c[label] == revenue_subquery.c[label] for label in dimension_labels]
    )

    final_query = (
        select(
            *[groups_subquery.c[label] for label in dimension_labels],
            sheep_subquery.c.sheep_count,
            sheep_subquery.c.avg_weight,
            sheep_subquery.c.avg_milk,
            cost_subquery.c.total_cost,
            revenue_subquery.c.total_revenue,
        )
        .select_from(groups_subquery)
        .outerjoin(sheep_subquery, join_condition_sheep)
        .outerjoin(cost_subquery, join_condition_cost)
        .outerjoin(revenue_subquery, join_condition_revenue)
        .order_by(*[groups_subquery.c[label] for label in dimension_labels])
    )

    rows = db.session.execute(final_query).all()
    if not rows:
        result = {'items': [], 'metrics': request_model.metrics}
        set_bi_cache(current_user.id, wrapped_payload, result)
        return {'data': result, 'status': 200}

    response_items = []
    for row in rows:
        mapping = getattr(row, '_mapping', row)
        group_key_raw = [mapping[label] for label in dimension_labels]
        normalized_key = []
        for dimension, value in zip(dimension_labels, group_key_raw):
            if dimension == 'lactation_number' and (value is None or value == -1):
                normalized_key.append(None)
            elif dimension != 'lactation_number' and value == '未填寫':
                normalized_key.append(None)
            else:
                normalized_key.append(value)
        sheep_count = mapping['sheep_count'] or 0
        avg_weight = mapping['avg_weight']
        avg_milk = mapping['avg_milk']
        total_cost = mapping['total_cost'] or Decimal('0')
        total_revenue = mapping['total_revenue'] or Decimal('0')
        net_profit = total_revenue - total_cost
        cost_per_head = (total_cost / sheep_count) if sheep_count else None
        revenue_per_head = (total_revenue / sheep_count) if sheep_count else None

        item = {label: value for label, value in zip(dimension_labels, normalized_key)}
        metrics_payload = {
            'sheep_count': sheep_count,
            'avg_weight': float(avg_weight) if avg_weight is not None else None,
            'avg_milk_yield': float(avg_milk) if avg_milk is not None else None,
            'total_cost': _serialize_decimal(total_cost),
            'total_revenue': _serialize_decimal(total_revenue),
            'net_profit': _serialize_decimal(net_profit),
            'cost_per_head': _serialize_decimal(cost_per_head),
            'revenue_per_head': _serialize_decimal(revenue_per_head),
        }
        item['metrics'] = {metric: metrics_payload.get(metric) for metric in request_model.metrics}
        response_items.append(item)

    result = {
        'items': response_items,
        'metrics': request_model.metrics,
    }
    set_bi_cache(current_user.id, wrapped_payload, result)
    return {'data': result, 'status': 200}


def _time_group_expression(model: type[CostEntry] | type[RevenueEntry], group_by: str) -> list[ColumnElement]:
    if group_by == 'none':
        return []
    if group_by == 'month':
        bind = db.session.get_bind()
        dialect_name = getattr(bind.dialect, 'name', 'sqlite') if bind is not None else 'sqlite'
        if dialect_name == 'sqlite':
            return [func.strftime('%Y-%m', model.recorded_at).label('period')]
        return [func.date_trunc('month', model.recorded_at).label('period')]
    if group_by in _DIMENSION_CONFIG:
        expr = _dimension_expression(model, group_by).label(group_by)
        return [expr]
    if group_by == 'category':
        return [model.category.label('category')]
    raise ValueError('不支援的分組方式')


def _cost_benefit(payload: dict) -> dict:
    try:
        request_model = CostBenefitRequest(**payload)
    except ValidationError as exc:
        return {'error': create_error_response('請求資料驗證失敗', exc.errors()), 'status': 400}

    wrapped_payload = {'endpoint': 'cost-benefit', 'payload': request_model.model_dump()}
    cached = get_bi_cache(current_user.id, wrapped_payload)
    if cached:
        return {'data': cached, 'status': 200}

    if not check_bi_rate_limit(current_user.id, 'cost-benefit'):
        return {'error': create_error_response('查詢次數過多，請稍後再試'), 'status': 429}

    group_expr_cost = _time_group_expression(CostEntry, request_model.group_by)
    cost_query = select(
        *group_expr_cost,
        func.sum(CostEntry.amount).label('total_cost'),
        func.count(func.distinct(CostEntry.sheep_id)).label('sheep_incurred'),
    )
    cost_query = _apply_finance_filters(cost_query, CostEntry, request_model.filters, request_model.time_range)
    if group_expr_cost:
        cost_query = cost_query.group_by(*group_expr_cost)
    cost_subquery = cost_query.subquery('cost_benefit')

    group_expr_revenue = _time_group_expression(RevenueEntry, request_model.group_by)
    revenue_query = select(
        *group_expr_revenue,
        func.sum(RevenueEntry.amount).label('total_revenue'),
        func.count(func.distinct(RevenueEntry.sheep_id)).label('sheep_served'),
    )
    revenue_query = _apply_finance_filters(revenue_query, RevenueEntry, request_model.filters, request_model.time_range)
    if group_expr_revenue:
        revenue_query = revenue_query.group_by(*group_expr_revenue)
    revenue_subquery = revenue_query.subquery('revenue_benefit')

    if request_model.group_by == 'none':
        cost_row = db.session.execute(cost_query).first()
        revenue_row = db.session.execute(revenue_query).first()
        total_cost = (cost_row._mapping['total_cost'] if cost_row else None) or Decimal('0')
        total_revenue = (revenue_row._mapping['total_revenue'] if revenue_row else None) or Decimal('0')
        sheep_count = max(
            (cost_row._mapping['sheep_incurred'] if cost_row else 0) or 0,
            (revenue_row._mapping['sheep_served'] if revenue_row else 0) or 0,
        )
        net_profit = total_revenue - total_cost
        summary_decimal = {
            'total_cost': total_cost,
            'total_revenue': total_revenue,
            'net_profit': net_profit,
        }
        summary = {key: float(value) for key, value in summary_decimal.items()}
        item_metrics = {
            'total_cost': _serialize_decimal(total_cost),
            'total_revenue': _serialize_decimal(total_revenue),
            'net_profit': _serialize_decimal(net_profit),
        }
        if 'avg_cost_per_head' in request_model.metrics:
            item_metrics['avg_cost_per_head'] = _serialize_decimal((total_cost / sheep_count) if sheep_count else None)
        if 'avg_revenue_per_head' in request_model.metrics:
            item_metrics['avg_revenue_per_head'] = _serialize_decimal((total_revenue / sheep_count) if sheep_count else None)
        items = [
            {
                'group': '總計',
                'metrics': item_metrics,
            }
        ] if (total_cost or total_revenue or sheep_count) else []
    else:
        group_by = request_model.group_by
        if group_by == 'month':
            group_labels = ['period']
        else:
            group_labels = [group_by]
        groups_query = select(*[cost_subquery.c[label] for label in group_labels]).select_from(cost_subquery)
        groups_query = groups_query.union(
            select(*[revenue_subquery.c[label] for label in group_labels]).select_from(revenue_subquery)
        )
        groups_subquery = groups_query.subquery('benefit_groups')

        join_condition_cost = and_(
            *[groups_subquery.c[label] == cost_subquery.c[label] for label in group_labels]
        )
        join_condition_revenue = and_(
            *[groups_subquery.c[label] == revenue_subquery.c[label] for label in group_labels]
        )

        final_query = (
            select(
                *[groups_subquery.c[label] for label in group_labels],
                cost_subquery.c.total_cost,
                revenue_subquery.c.total_revenue,
                cost_subquery.c.sheep_incurred,
                revenue_subquery.c.sheep_served,
            )
            .select_from(
                groups_subquery.outerjoin(cost_subquery, join_condition_cost).outerjoin(
                    revenue_subquery, join_condition_revenue
                )
            )
            .order_by(*[groups_subquery.c[label] for label in group_labels])
        )
        rows = db.session.execute(final_query).all()

        summary_decimal = {
            'total_cost': Decimal('0'),
            'total_revenue': Decimal('0'),
            'net_profit': Decimal('0'),
        }
        items = []
        for row in rows:
            mapping = getattr(row, '_mapping', row)
            total_cost = mapping['total_cost'] or Decimal('0')
            total_revenue = mapping['total_revenue'] or Decimal('0')
            sheep_count = max(mapping['sheep_incurred'] or 0, mapping['sheep_served'] or 0)
            net_profit = total_revenue - total_cost
            summary_decimal['total_cost'] += total_cost
            summary_decimal['total_revenue'] += total_revenue
            summary_decimal['net_profit'] += net_profit

            group_values = [mapping[label] for label in group_labels]
            group_display = ' / '.join('未指定' if value in (None, '未填寫') else str(value) for value in group_values)
            metrics = {
                'total_cost': _serialize_decimal(total_cost),
                'total_revenue': _serialize_decimal(total_revenue),
                'net_profit': _serialize_decimal(net_profit),
            }
            if 'avg_cost_per_head' in request_model.metrics:
                metrics['avg_cost_per_head'] = _serialize_decimal((total_cost / sheep_count) if sheep_count else None)
            if 'avg_revenue_per_head' in request_model.metrics:
                metrics['avg_revenue_per_head'] = _serialize_decimal((total_revenue / sheep_count) if sheep_count else None)
            items.append({'group': group_display, 'metrics': metrics})

        summary = {key: float(value) for key, value in summary_decimal.items()}

    result = {
        'summary': summary,
        'items': items,
        'metrics': request_model.metrics,
    }
    set_bi_cache(current_user.id, wrapped_payload, result)
    return {'data': result, 'status': 200}


@bp.route('/cohort-analysis', methods=['POST'])
@login_required
def cohort_analysis():
    payload = request.get_json(silent=True) or {}
    result = _cohort_analysis(payload)
    if 'error' in result:
        return jsonify(result['error']), result['status']
    return jsonify(result['data']), result['status']


@bp.route('/cost-benefit', methods=['POST'])
@login_required
def cost_benefit():
    payload = request.get_json(silent=True) or {}
    result = _cost_benefit(payload)
    if 'error' in result:
        return jsonify(result['error']), result['status']
    return jsonify(result['data']), result['status']

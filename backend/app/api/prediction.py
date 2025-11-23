from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Sheep, SheepHistoricalData
from app.utils import call_gemini_api
from datetime import datetime, date, timedelta
from pathlib import Path
import importlib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import json

bp = Blueprint('prediction', __name__)

MODEL_DIR = Path(__file__).resolve().parents[2] / 'models'
LGBM_MODEL_FILES = {
    'main': 'sheep_growth_lgbm.joblib',
    'q10': 'sheep_growth_lgbm_q10.joblib',
    'q90': 'sheep_growth_lgbm_q90.joblib'
}
METADATA_PATH = MODEL_DIR / 'sheep_growth_lgbm_metadata.json'

try:
    with open(METADATA_PATH, 'r', encoding='utf-8') as meta_file:
        LGBM_METADATA = json.load(meta_file)
except FileNotFoundError:
    LGBM_METADATA = None

LGBM_FEATURE_ORDER = LGBM_METADATA.get('feature_order', []) if LGBM_METADATA else []
LGBM_CATEGORICAL_FEATURE_LIST = LGBM_METADATA.get('categorical_features', []) if LGBM_METADATA else []
LGBM_CATEGORICAL_FEATURES = set(LGBM_CATEGORICAL_FEATURE_LIST)
AGE_DAYS_P90 = LGBM_METADATA.get('age_days_p90') if LGBM_METADATA else None
AGE_DAYS_P95 = LGBM_METADATA.get('age_days_p95') if LGBM_METADATA else None
AGE_DAYS_P99 = LGBM_METADATA.get('age_days_p99') if LGBM_METADATA else None
AGE_DAYS_WARNING_THRESHOLD = AGE_DAYS_P95 or AGE_DAYS_P90 or 365
AGE_DAYS_OOD_THRESHOLD = AGE_DAYS_P99 or AGE_DAYS_P95 or 600
MAX_GAIN_MULTIPLIER = 3.0
MAX_WEIGHT_DIFF_ABS = 15.0
MAX_WEIGHT_DIFF_RATIO = 0.35
MAX_ELIGIBLE_AGE_DAYS = 365
MIN_ELIGIBLE_AGE_DAYS = 60


def _parse_birth_date(birth_date_str):
    if not birth_date_str:
        return None
    try:
        return datetime.strptime(birth_date_str, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _validate_prediction_applicability(sheep, target_days):
    birth_date = _parse_birth_date(getattr(sheep, 'BirthDate', None))
    if birth_date is None:
        return None, None, "無法預測：羊隻缺少有效的出生日期"

    current_days = (date.today() - birth_date).days
    if current_days < 0:
        return None, None, "無法預測：羊隻出生日期晚於今天，請檢查資料"

    if current_days < MIN_ELIGIBLE_AGE_DAYS:
        remaining = max(MIN_ELIGIBLE_AGE_DAYS - current_days, 0)
        return birth_date, current_days, (
            f"本系統需羊隻至少滿 {MIN_ELIGIBLE_AGE_DAYS} 天，目前僅 {current_days} 天，距離門檻尚有 {remaining} 天"
        )

    if current_days > MAX_ELIGIBLE_AGE_DAYS:
        return None, current_days, (
            f"本系統目前僅支援出生一年內（≤{MAX_ELIGIBLE_AGE_DAYS} 天）的幼年羊隻預測，該羊隻已 {current_days} 天"
        )

    return birth_date, current_days, None

RAW_CATEGORY_ALIASES = {
    'Sex': {
        '__default__': 3.0,
        '1': 1.0,
        '1.0': 1.0,
        '母': 1.0,
        '母羊': 1.0,
        '雌': 1.0,
        'f': 1.0,
        'female': 1.0,
        '2': 2.0,
        '2.0': 2.0,
        '公': 2.0,
        '公羊': 2.0,
        '雄': 2.0,
        'm': 2.0,
        'male': 2.0,
        '3': 3.0,
        '3.0': 3.0,
        '閹': 3.0,
        '閹羊': 3.0,
        'unknown': 3.0,
        '未指定': 3.0,
        '不詳': 3.0
    },
    'Breed': {
        '__default__': 'Fx',
        '努比亞': 'NU',
        '努比亞羊': 'NU',
        'nubian': 'NU',
        'nu': 'NU',
        '波爾': 'BO',
        '波爾羊': 'BO',
        'bo': 'BO',
        'boer': 'BO',
        'f1': 'F1',
        'f1雜交': 'F1',
        'f2': 'F2',
        'f2雜交': 'F2',
        'f3': 'F3',
        'f3雜交': 'F3',
        'fx': 'Fx',
        '雜交': 'Fx',
        '混種': 'Fx',
        '混血': 'Fx',
        '混合': 'Fx',
        '台灣黑山羊': 'Fx',
        '阿爾拜因': 'RB',
        '阿爾拜因羊': 'RB',
        'alpine': 'RB',
        'rb': 'RB'
    },
    'ReproStatus': {
        '__default__': '未配種',
        '懷孕': '懷孕',
        '懷孕中': '懷孕',
        '懷孕早期': '懷孕',
        '懷孕晚期': '懷孕',
        'pregnant': '懷孕',
        'gestating': '懷孕',
        'gestating_early': '懷孕',
        'gestating_late': '懷孕',
        'gestation': '懷孕',
        '未配種': '未配種',
        '未懷孕': '未配種',
        'not bred': '未配種',
        'maintenance': '未配種',
        '維持期': '未配種',
        'growing_young': '未配種',
        '生長前期': '未配種',
        'growing_finishing': '未配種',
        '生長育肥期': '未配種',
        'dry_period': '未配種',
        '乾乳期': '未配種',
        '乾乳': '未配種',
        'breeding_male_active': '未配種',
        'breeding_male_non_active': '未配種',
        '配種期公羊': '未配種',
        '非配種期公羊': '未配種',
        'fiber_producing': '未配種',
        '產毛期': '未配種',
        'other_status': '未配種',
        '泌乳': '泌乳',
        '泌乳中': '泌乳',
        '泌乳早期': '泌乳',
        '泌乳高峰期': '泌乳',
        '泌乳中期': '泌乳',
        '泌乳晚期': '泌乳',
        'lactating': '泌乳',
        'lactating_early': '泌乳',
        'lactating_peak': '泌乳',
        'lactating_mid': '泌乳',
        'lactating_late': '泌乳'
    }
}

CATEGORY_DEFAULTS = {key: aliases.get('__default__') for key, aliases in RAW_CATEGORY_ALIASES.items()}

def _build_alias_lookup():
    lookup = {}
    for field, aliases in RAW_CATEGORY_ALIASES.items():
        field_lookup = {}
        for alias, target in aliases.items():
            if alias == '__default__' or alias is None:
                continue
            alias_str = str(alias)
            normalized_keys = {
                alias_str,
                alias_str.strip(),
                alias_str.lower(),
                alias_str.strip().lower(),
                alias_str.upper(),
                alias_str.strip().upper()
            }
            for key in normalized_keys:
                if key:
                    field_lookup[key] = target
        lookup[field] = field_lookup
    return lookup

CATEGORY_ALIAS_LOOKUP = _build_alias_lookup()
DISPLAY_FIELD_NAMES = {
    'Sex': '性別',
    'Breed': '品種',
    'ReproStatus': '生理狀態'
}

_lgbm_models = {}
_lgbm_load_error = None
_lgbm_category_levels = {}


def _postprocess_lgbm_model(model):
    """調整 LightGBM 模型推論參數，避免冗餘警告。"""
    if not model:
        return
    try:
        model.set_params(min_child_samples=50, verbosity=-1)
    except Exception:
        pass


def _ensure_lgbm_models():
    """Lazy-load LightGBM 模型，供預測使用。"""
    global _lgbm_models, _lgbm_load_error, _lgbm_category_levels

    if _lgbm_models:
        return True
    if _lgbm_load_error:
        return False

    if importlib.util.find_spec('lightgbm') is None:  # pragma: no cover - 需實際環境才會觸發
        _lgbm_load_error = "LightGBM 套件未安裝"
        if current_app:
            current_app.logger.warning(_lgbm_load_error)
        return False

    loaded_models = {}
    main_model_path = MODEL_DIR / LGBM_MODEL_FILES['main']
    if not main_model_path.exists():
        _lgbm_load_error = f"找不到主要模型檔案 {main_model_path.name}"
        if current_app:
            current_app.logger.warning(_lgbm_load_error)
        return False

    try:
        loaded_models['main'] = joblib.load(main_model_path)
        _postprocess_lgbm_model(loaded_models['main'])

        _lgbm_category_levels = {}
        booster = getattr(loaded_models['main'], 'booster_', None)
        category_info = getattr(booster, 'pandas_categorical', None) if booster else None
        if category_info and LGBM_CATEGORICAL_FEATURE_LIST:
            _lgbm_category_levels = dict(zip(LGBM_CATEGORICAL_FEATURE_LIST, category_info))

        for key in ('q10', 'q90'):
            model_path = MODEL_DIR / LGBM_MODEL_FILES[key]
            if model_path.exists():
                loaded_models[key] = joblib.load(model_path)
                _postprocess_lgbm_model(loaded_models[key])
            else:
                message = f"量化模型檔案 {model_path.name} 不存在"
                if current_app:
                    current_app.logger.warning(message)
    except Exception as exc:  # pragma: no cover - 需實際模型才會觸發
        _lgbm_load_error = f"載入 LightGBM 模型失敗: {exc}"
        if current_app:
            current_app.logger.warning(_lgbm_load_error)
        return False

    _lgbm_models = loaded_models
    return True


def _coerce_numeric(value, field_name, warnings):
    """將輸入轉為 float，若缺值則使用 np.nan 並記錄警告。"""
    if value is None:
        warnings.append(f"{field_name} 缺值，已使用 NaN")
        return np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        warnings.append(f"{field_name} 無法轉為數值，已使用 NaN")
        return np.nan


def _coerce_categorical(value, field_name, warnings):
    """將輸入轉為字串；缺值時以 'Unknown' 取代並記錄警告。"""
    if value in (None, ''):
        warnings.append(f"{field_name} 缺值，已以 'Unknown' 取代")
        return 'Unknown'
    return str(value)


def _normalize_category(field_name, raw_value, warnings):
    """將輸入映射至 LightGBM 訓練時使用的分類值。"""
    display_name = DISPLAY_FIELD_NAMES.get(field_name, field_name)
    lookup = CATEGORY_ALIAS_LOOKUP.get(field_name, {})
    default_value = CATEGORY_DEFAULTS.get(field_name)
    allowed_values = set(_lgbm_category_levels.get(field_name, [])) if _lgbm_category_levels else set()

    if raw_value in (None, ''):
        if default_value is not None:
            warnings.append(f"{display_name} 缺值，已使用模型預設分類 {default_value}")
            return default_value
        return raw_value

    value_str = str(raw_value).strip()
    if not value_str:
        if default_value is not None:
            warnings.append(f"{display_name} 缺值，已使用模型預設分類 {default_value}")
            return default_value
        return raw_value

    normalized = lookup.get(value_str)
    if normalized is None:
        normalized = lookup.get(value_str.lower())

    if normalized is None and field_name == 'Breed':
        trimmed = value_str
        for token in ('山羊', '公羊', '母羊', '羊'):
            trimmed = trimmed.replace(token, '')
        trimmed = trimmed.strip()
        if trimmed and trimmed != value_str:
            normalized = lookup.get(trimmed) or lookup.get(trimmed.lower())

    if normalized is None and field_name == 'Sex':
        try:
            normalized = float(value_str)
        except (TypeError, ValueError):
            normalized = None

    if normalized is None:
        if field_name == 'Breed':
            normalized = value_str.upper()
        elif field_name == 'ReproStatus':
            normalized = value_str
        else:
            normalized = value_str

    if field_name == 'Sex' and normalized is not None:
        try:
            normalized = float(normalized)
        except (TypeError, ValueError):
            normalized = default_value

    if field_name == 'Breed' and isinstance(normalized, str):
        normalized = normalized.upper()

    if field_name == 'ReproStatus' and isinstance(normalized, str):
        normalized = normalized.strip()
        normalized = lookup.get(normalized) or lookup.get(normalized.lower()) or normalized

    if allowed_values:
        if normalized not in allowed_values:
            fallback = default_value if default_value in allowed_values else (next(iter(allowed_values)) if allowed_values else normalized)
            warnings.append(f"{display_name} 值 '{value_str}' 未匹配模型分類，已改用 {fallback}")
            normalized = fallback

    if normalized is None and default_value is not None:
        warnings.append(f"{display_name} 值 '{value_str}' 未能辨識，已改用 {default_value}")
        normalized = default_value

    return normalized


def _determine_seasonality(target_date):
    """根據日期回傳月份編號 (1-12)。"""
    return target_date.month


def _build_lgbm_dataframe(sheep, future_days, future_date):
    """組裝 LightGBM 模型所需的特徵資料。"""
    if not LGBM_FEATURE_ORDER:
        return None, "缺少 LightGBM 特徵定義"

    warnings = []
    feature_values = {}

    feature_values['AgeDays'] = _coerce_numeric(future_days, 'AgeDays', warnings)
    feature_values['BirWei'] = _coerce_numeric(getattr(sheep, 'BirWei', None), 'BirWei', warnings)
    feature_values['Sex'] = _normalize_category('Sex', getattr(sheep, 'Sex', None), warnings)
    feature_values['Breed'] = _normalize_category('Breed', getattr(sheep, 'Breed', None), warnings)
    feature_values['LittleSize'] = _coerce_numeric(getattr(sheep, 'LittleSize', None), 'LittleSize', warnings)
    feature_values['Lactation'] = _coerce_numeric(getattr(sheep, 'Lactation', None), 'Lactation', warnings)
    days_in_milk_raw = getattr(sheep, 'DaysInMilk', None)
    if days_in_milk_raw in (None, ''):
        days_in_milk_raw = -1
    days_in_milk_value = _coerce_numeric(days_in_milk_raw, 'DaysInMilk', warnings)
    if not np.isfinite(days_in_milk_value):
        days_in_milk_value = -1
    feature_values['DaysInMilk'] = days_in_milk_value

    repro_status = getattr(sheep, 'ReproStatus', None) or getattr(sheep, 'status', None) or '未配種'
    feature_values['ReproStatus'] = _normalize_category('ReproStatus', repro_status, warnings)

    feature_values['Seasonality'] = _coerce_numeric(_determine_seasonality(future_date), 'Seasonality', warnings)

    ordered_row = [feature_values.get(feature, np.nan) for feature in LGBM_FEATURE_ORDER]
    dataframe = pd.DataFrame([ordered_row], columns=LGBM_FEATURE_ORDER)

    if _lgbm_category_levels:
        for feature, categories in _lgbm_category_levels.items():
            if feature in dataframe.columns and categories:
                dataframe[feature] = pd.Categorical(dataframe[feature], categories=categories)

    return dataframe, '；'.join(warnings) if warnings else None


def _compute_prediction_metrics(sheep, weight_data, target_days, birth_date):
    """根據歷史體重數據計算預測結果、曲線與統計指標。"""
    if not weight_data or not birth_date:
        return None, "無有效的體重記錄可用於預測"

    dates = []
    weights = []
    for record in weight_data:
        try:
            record_date = datetime.strptime(record['record_date'], '%Y-%m-%d').date()
            weight_value = float(record['value'])
        except (KeyError, TypeError, ValueError):
            continue
        days_from_birth = (record_date - birth_date).days
        dates.append(days_from_birth)
        weights.append(weight_value)

    if not dates:
        return None, "無有效的體重記錄可用於預測"

    X = np.array(dates).reshape(-1, 1)
    y = np.array(weights)

    model = LinearRegression()
    model.fit(X, y)

    current_days = (date.today() - birth_date).days if birth_date else max(dates)
    future_days = current_days + target_days
    linear_average_daily_gain = float(model.coef_[0])
    latest_weight = float(weights[-1]) if weights else float('nan')
    first_weight = float(weights[0]) if weights else float('nan')

    today = date.today()
    day_offsets = list(range(0, target_days + 1))
    age_series = [current_days + offset for offset in day_offsets]
    future_dates = [today + timedelta(days=offset) for offset in day_offsets] if birth_date else [None for _ in day_offsets]

    linear_series = model.predict(np.array(age_series).reshape(-1, 1))
    linear_series = [float(value) for value in linear_series]

    linear_daily_forecasts = []
    for idx, offset in enumerate(day_offsets):
        forecast_date = future_dates[idx]
        linear_daily_forecasts.append({
            'day_offset': int(offset),
            'age_days': int(age_series[idx]),
            'date': forecast_date.strftime('%Y-%m-%d') if forecast_date else None,
            'predicted_weight': max(linear_series[idx], 0.0)
        })

    linear_predicted_weight = linear_daily_forecasts[-1]['predicted_weight']
    future_date = future_dates[-1] if future_dates else None

    metrics = {
        'predicted_weight': linear_predicted_weight,
        'average_daily_gain': 0.0,
        'prediction_source': 'linear_regression',
        'pred_interval': {'q10': None, 'q90': None},
        'warning_messages': [],
        'prediction_warning': None,
        'future_days': future_days,
        'future_date': future_date,
        'latest_weight': latest_weight,
        'linear_predicted_weight': linear_predicted_weight,
        'current_days': current_days,
        'daily_forecasts': linear_daily_forecasts,
        'daily_confidence_band': None
    }

    if target_days > 0 and np.isfinite(latest_weight) and np.isfinite(linear_predicted_weight):
        metrics['average_daily_gain'] = (linear_predicted_weight - latest_weight) / target_days
    elif np.isfinite(linear_average_daily_gain):
        metrics['average_daily_gain'] = linear_average_daily_gain

    if target_days > 0 and not np.isfinite(metrics['average_daily_gain']):
        metrics['average_daily_gain'] = 0.0

    age_ood_threshold = AGE_DAYS_OOD_THRESHOLD
    skip_lgbm_due_to_age = False

    if birth_date:
        if age_ood_threshold and future_days > age_ood_threshold:
            skip_lgbm_due_to_age = True
            metrics['warning_messages'].append(
                f"LightGBM 訓練資料主要涵蓋幼齡羊（<= {int(age_ood_threshold)} 天），此預測超出範圍，已改用線性迴歸"
            )

    if skip_lgbm_due_to_age and np.isfinite(linear_average_daily_gain) and np.isfinite(first_weight):
        adjusted_linear_prediction = first_weight + linear_average_daily_gain * target_days
        if np.isfinite(adjusted_linear_prediction):
            adjusted_linear_prediction = max(adjusted_linear_prediction, 0.0)
            linear_daily_forecasts[-1]['predicted_weight'] = adjusted_linear_prediction
            metrics['daily_forecasts'] = linear_daily_forecasts
            metrics['linear_predicted_weight'] = adjusted_linear_prediction
            metrics['predicted_weight'] = adjusted_linear_prediction

    if birth_date and not skip_lgbm_due_to_age and _ensure_lgbm_models():
        try:
            main_model = _lgbm_models.get('main')
            if main_model is None:
                metrics['warning_messages'].append('主要 LightGBM 模型尚未就緒，已使用線性迴歸')
            else:
                q10_model = _lgbm_models.get('q10')
                q90_model = _lgbm_models.get('q90')

                lgbm_daily_forecasts = []
                lgbm_confidence_band = []
                recorded_feature_warnings = set()

                for idx, offset in enumerate(day_offsets):
                    day_age = age_series[idx]
                    day_date = future_dates[idx]
                    lgbm_input, feature_warning = _build_lgbm_dataframe(sheep, day_age, day_date)

                    if feature_warning:
                        for warning_msg in feature_warning.split('；'):
                            warning_msg = warning_msg.strip()
                            if warning_msg and warning_msg not in recorded_feature_warnings:
                                metrics['warning_messages'].append(warning_msg)
                                recorded_feature_warnings.add(warning_msg)

                    if lgbm_input is None:
                        lgbm_daily_forecasts = None
                        break

                    pred_value = float(main_model.predict(lgbm_input)[0])
                    q10_value = float(q10_model.predict(lgbm_input)[0]) if q10_model else None
                    q90_value = float(q90_model.predict(lgbm_input)[0]) if q90_model else None

                    if q10_value is not None and q90_value is not None and q10_value > q90_value:
                        q10_value, q90_value = q90_value, q10_value

                    forecast_entry = {
                        'day_offset': int(offset),
                        'age_days': int(day_age),
                        'date': day_date.strftime('%Y-%m-%d') if day_date else None,
                        'predicted_weight': max(pred_value, 0.0)
                    }
                    lgbm_daily_forecasts.append(forecast_entry)

                    band_entry = {
                        'day_offset': int(offset),
                        'age_days': int(day_age),
                        'date': day_date.strftime('%Y-%m-%d') if day_date else None,
                        'lower': max(q10_value, 0.0) if q10_value is not None else None,
                        'upper': max(q90_value, 0.0) if q90_value is not None else None
                    }
                    lgbm_confidence_band.append(band_entry)

                if lgbm_daily_forecasts is not None:
                    final_lgbm_weight = lgbm_daily_forecasts[-1]['predicted_weight']
                    final_q10 = lgbm_confidence_band[-1]['lower'] if lgbm_confidence_band else None
                    final_q90 = lgbm_confidence_band[-1]['upper'] if lgbm_confidence_band else None

                    breed_ranges = get_breed_reference_ranges(getattr(sheep, 'Breed', None), (future_days // 30) if future_days else None)
                    max_allowed_gain = None
                    if breed_ranges and isinstance(breed_ranges, dict):
                        max_allowed_gain = breed_ranges.get('max')

                    gain_candidate = None
                    if target_days > 0 and np.isfinite(latest_weight) and np.isfinite(final_lgbm_weight):
                        gain_candidate = (final_lgbm_weight - latest_weight) / target_days
                    elif np.isfinite(linear_average_daily_gain):
                        gain_candidate = linear_average_daily_gain

                    fallback_reasons = []
                    if max_allowed_gain is not None and gain_candidate is not None:
                        if gain_candidate > max_allowed_gain * MAX_GAIN_MULTIPLIER:
                            fallback_reasons.append(
                                f"LightGBM 預測平均日增重 {gain_candidate:.3f} kg/天，大幅高於品種參考上限 {max_allowed_gain:.3f}"
                            )

                    diff_threshold = MAX_WEIGHT_DIFF_ABS
                    if np.isfinite(latest_weight):
                        diff_threshold = max(diff_threshold, latest_weight * MAX_WEIGHT_DIFF_RATIO)

                    if abs(final_lgbm_weight - metrics['linear_predicted_weight']) > diff_threshold:
                        fallback_reasons.append(
                            f"LightGBM 預測體重 {final_lgbm_weight:.2f} kg 與線性趨勢 {metrics['linear_predicted_weight']:.2f} kg 差異過大"
                        )

                    if fallback_reasons:
                        metrics['warning_messages'].append('；'.join(fallback_reasons) + '，已改用線性迴歸')
                        metrics['predicted_weight'] = metrics['linear_predicted_weight']
                        metrics['prediction_source'] = 'linear_regression'
                        metrics['pred_interval'] = {'q10': None, 'q90': None}
                        metrics['daily_forecasts'] = linear_daily_forecasts
                        metrics['daily_confidence_band'] = None
                        metrics['average_daily_gain'] = (
                            (metrics['predicted_weight'] - latest_weight) / target_days
                            if target_days > 0 and np.isfinite(latest_weight)
                            else (linear_average_daily_gain if np.isfinite(linear_average_daily_gain) else metrics['average_daily_gain'])
                        )
                    else:
                        metrics['prediction_source'] = 'lightgbm'
                        metrics['predicted_weight'] = final_lgbm_weight
                        metrics['pred_interval'] = {'q10': final_q10, 'q90': final_q90}
                        metrics['daily_forecasts'] = lgbm_daily_forecasts
                        metrics['daily_confidence_band'] = lgbm_confidence_band
                        if target_days > 0 and np.isfinite(latest_weight) and np.isfinite(final_lgbm_weight):
                            metrics['average_daily_gain'] = (final_lgbm_weight - latest_weight) / target_days
                        elif gain_candidate is not None and np.isfinite(gain_candidate):
                            metrics['average_daily_gain'] = gain_candidate

                else:
                    metrics['warning_messages'].append('無法生成 LightGBM 特徵，已使用線性迴歸')
        except Exception as exc:  # pragma: no cover - 需實際模型才會觸發
            current_app.logger.warning(f"LightGBM 預測失敗，使用線性迴歸備援: {exc}")
            metrics['warning_messages'].append(f"LightGBM 預測失敗: {exc}")
            metrics['predicted_weight'] = metrics['linear_predicted_weight']
            metrics['average_daily_gain'] = (
                (metrics['predicted_weight'] - latest_weight) / target_days
                if target_days > 0 and np.isfinite(latest_weight)
                else (linear_average_daily_gain if np.isfinite(linear_average_daily_gain) else metrics['average_daily_gain'])
            )
            metrics['pred_interval'] = {'q10': None, 'q90': None}
            metrics['prediction_source'] = 'linear_regression'
    elif not birth_date:
        metrics['warning_messages'].append('羊隻缺少出生日期資料，已使用線性迴歸預測')
    elif _lgbm_load_error:
        metrics['warning_messages'].append(_lgbm_load_error)

    metrics['predicted_weight'] = max(metrics['predicted_weight'], 0.0)

    if metrics['daily_forecasts']:
        for entry in metrics['daily_forecasts']:
            entry['predicted_weight'] = max(entry['predicted_weight'], 0.0)

    if metrics['daily_confidence_band']:
        for entry in metrics['daily_confidence_band']:
            if entry['lower'] is not None:
                entry['lower'] = max(entry['lower'], 0.0)
            if entry['upper'] is not None:
                entry['upper'] = max(entry['upper'], 0.0)

    for key in ('q10', 'q90'):
        if metrics['pred_interval'][key] is not None:
            metrics['pred_interval'][key] = max(metrics['pred_interval'][key], 0.0)

    metrics['prediction_warning'] = '；'.join(metrics['warning_messages']) if metrics['warning_messages'] else None
    metrics.pop('warning_messages', None)
    return metrics, None

def data_quality_check(weight_records):
    """
    數據品質檢驗函式
    返回數據品質報告物件
    """
    if not weight_records:
        return {
            'status': 'Error',
            'message': '無體重記錄',
            'details': {
                'record_count': 0,
                'time_span_days': 0,
                'outliers_count': 0
            }
        }

    record_count = len(weight_records)

    # 檢查數據點數量
    if record_count < 3:
        return {
            'status': 'Error',
            'message': f'數據點不足，至少需要3筆記錄才能進行預測分析，目前僅有{record_count}筆',
            'details': {
                'record_count': record_count,
                'time_span_days': 0,
                'outliers_count': 0
            }
        }

    # 計算時間跨度
    dates = [datetime.strptime(record['record_date'], '%Y-%m-%d') for record in weight_records]
    dates.sort()
    time_span_days = (dates[-1] - dates[0]).days

    # 異常值檢測
    weights = [float(record['value']) for record in weight_records]
    mean_weight = np.mean(weights)
    std_weight = np.std(weights)
    outliers = [w for w in weights if abs(w - mean_weight) > 3 * std_weight]
    outliers_count = len(outliers)

    # 生成品質報告
    if time_span_days < 15:
        status = 'Warning'
        message = f'數據點充足({record_count}筆)但時間跨度較短({time_span_days}天)'
        if outliers_count > 0:
            message += f'，且偵測到{outliers_count}筆潛在異常值'
    elif outliers_count > 0:
        status = 'Warning'
        message = f'數據品質良好({record_count}筆，跨度{time_span_days}天)，但偵測到{outliers_count}筆潛在異常值'
    else:
        status = 'Good'
        message = f'數據品質優良，共{record_count}筆記錄，時間跨度{time_span_days}天'

    return {
        'status': status,
        'message': message,
        'details': {
            'record_count': record_count,
            'time_span_days': time_span_days,
            'outliers_count': outliers_count
        }
    }

def calculate_age_in_months(birth_date):
    """計算月齡"""
    if not birth_date:
        return None
    try:
        birth = datetime.strptime(birth_date, '%Y-%m-%d').date()
        today = date.today()
        return (today.year - birth.year) * 12 + today.month - birth.month
    except:
        return None

def get_breed_reference_ranges(breed, age_months):
    """
    根據品種和月齡提供參考日增重範圍
    這裡提供基本的參考值，實際應用中可以從資料庫或配置文件讀取
    """
    # 基本參考值 (公斤/天)
    ranges = {
        '努比亞': {'min': 0.08, 'max': 0.15},
        '阿爾拜因': {'min': 0.07, 'max': 0.13},
        '撒能': {'min': 0.09, 'max': 0.16},
        '波爾': {'min': 0.10, 'max': 0.18},
        '台灣黑山羊': {'min': 0.06, 'max': 0.12},
        'default': {'min': 0.07, 'max': 0.14}
    }
    
    # 根據月齡調整 (幼羊增重較快)
    if age_months and age_months < 6:
        multiplier = 1.3
    elif age_months and age_months < 12:
        multiplier = 1.1
    else:
        multiplier = 1.0
    
    base_range = ranges.get(breed, ranges['default'])
    return {
        'min': round(base_range['min'] * multiplier, 3),
        'max': round(base_range['max'] * multiplier, 3)
    }

@bp.route('/goats/<string:ear_tag>/prediction', methods=['GET'])
@login_required
def get_sheep_prediction(ear_tag):
    """取得羊隻生長預測"""
    try:
        # 獲取目標預測天數，預設30天
        target_days = request.args.get('target_days', 30, type=int)
        
        # 檢查目標天數範圍
        if target_days < 7 or target_days > 365:
            return jsonify(error="預測天數必須在7-365天之間"), 400
        
        # 需要前端提供 Gemini API 金鑰以產生第二階段 AI 分析
        api_key = request.headers.get('X-Api-Key')
        if not api_key:
            return jsonify(error="未提供API金鑰於請求頭中 (X-Api-Key)"), 401
        
        # 獲取羊隻資料
        sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_tag).first()
        if not sheep:
            return jsonify(error=f"找不到耳號為 {ear_tag} 的羊隻"), 404
        
        # 獲取體重歷史記錄
        weight_records = SheepHistoricalData.query.filter_by(
            sheep_id=sheep.id,
            record_type='Body_Weight_kg'
        ).order_by(SheepHistoricalData.record_date.asc()).all()
        
        birth_date, current_days, applicability_error = _validate_prediction_applicability(sheep, target_days)
        if applicability_error:
            return jsonify(error=applicability_error), 400

        # 轉換為字典格式
        weight_data = [record.to_dict() for record in weight_records]
        
        # 數據品質檢查
        data_quality_report = data_quality_check(weight_data)
        
        if data_quality_report['status'] == 'Error':
            return jsonify(
                error="數據不足以進行預測",
                data_quality_report=data_quality_report
            ), 400
        
        # 準備預測數據
        prediction_metrics, error_message = _compute_prediction_metrics(sheep, weight_data, target_days, birth_date)
        if error_message:
            return jsonify(error=error_message), 400

        predicted_weight = prediction_metrics['predicted_weight']
        average_daily_gain = prediction_metrics['average_daily_gain']
        pred_interval = prediction_metrics['pred_interval']
        prediction_source = prediction_metrics['prediction_source']
        prediction_warning = prediction_metrics['prediction_warning']

        # 計算月齡
        current_age_months = calculate_age_in_months(sheep.BirthDate)
        
        # 獲取品種參考範圍
        breed_ranges = get_breed_reference_ranges(sheep.Breed, current_age_months)

        model_label = 'LightGBM 模型' if prediction_source == 'lightgbm' else '線性回歸模型'
        if pred_interval['q10'] is not None and pred_interval['q90'] is not None:
            interval_text = f"{pred_interval['q10']:.2f} - {pred_interval['q90']:.2f} 公斤"
        else:
            interval_text = '暫無可用資料'
        
        # 準備 LLM 提示詞
        prompt = f"""# 角色扮演指令
你是一位資深的智慧牧場營養學專家「領頭羊博士」，兼具ESG永續經營的顧問視角。請用繁體中文，以專業、溫暖且數據驅動的語氣進行分析，並將各部分回覆控制在2-3句話內。

# 羊隻資料
- 耳號: {sheep.EarNum}
- 品種: {sheep.Breed or '未指定'}
- 性別: {sheep.Sex or '未指定'}
- 目前月齡: {current_age_months or '未知'} 個月

# 數據品質評估 (由我方系統提供)
- 數據品質狀況: {data_quality_report['status']}
- 評估說明: {data_quality_report['message']}

# 統計分析結果 (由我方系統提供)
- 預測目標: {target_days} 天後的體重
- 預測模型: {model_label}
- 預測體重: {predicted_weight:.2f} 公斤
- 模型平均日增重: {average_daily_gain:.3f} 公斤/天
- 預測信賴區間 (q10-q90): {interval_text}

# 領域知識錨點 (由我方系統提供)
- 參考指標: 根據文獻，{sheep.Breed or '一般山羊'}品種的山羊在此月齡，健康的日增重範圍約為 {breed_ranges['min']} 到 {breed_ranges['max']} 公斤/天。

# 你的任務
請基於以上所有資訊，特別是「數據品質評估」和「領域知識錨點」，生成一份包含以下三部分的分析報告：

1. **生長潛力解讀**: 結合數據品質，解讀預測體重。將「模型平均日增重」與「參考指標」進行比較，判斷其增長趨勢（例如：優於預期、符合標準、略顯緩慢、因數據品質有限建議謹慎看待）。
2. **飼養管理與ESG建議**: 根據生長情況，提供1-2項具體建議。**請務必在建議中融入ESG理念**，例如如何透過精準飼餵減少浪費（環境E），或如何調整管理方式提升動物福利（社會S）。
3. **透明度與提醒**: 根據數據品質，提供一個客製化的提醒。如果品質好，則肯定數據記錄的價值；如果品質差，則鼓勵用戶更頻繁、準確地記錄數據以獲得更可靠的分析。

請用 Markdown 格式回覆，並確保內容專業且易懂。"""

        # 調用 Gemini API
        try:
            ai_result = call_gemini_api(
                prompt,
                api_key,
                generation_config_override={"temperature": 0.6}
            )
        except Exception as ai_error:
            current_app.logger.warning(f"AI 分析失敗，使用備用分析: {ai_error}")
            # 提供備用分析
            ai_result = {
                'text': f"""## 🐐 生長潛力解讀
根據{model_label}分析，預測 {target_days} 天後體重為 **{predicted_weight:.2f} 公斤**。當前平均日增重為 **{average_daily_gain:.3f} 公斤/天**，與 {sheep.Breed or '一般山羊'} 品種參考範圍（{breed_ranges['min']}-{breed_ranges['max']} 公斤/天）相比{'符合標準' if breed_ranges['min'] <= average_daily_gain <= breed_ranges['max'] else '需要關注'}。

## 🌱 飼養管理與ESG建議
建議採用精準飼餵管理，根據個體生長狀況調整飼料配比，既能提升動物福利（S），又能減少飼料浪費實現環境永續（E）。

## 📊 透明度與提醒
{data_quality_report['message']}。預測信賴區間 (q10-q90)：{interval_text if interval_text != '暫無可用資料' else '暫無可用資料'}。建議持續記錄體重數據以提升預測準確性。"""
            }
        
        
        if "error" in ai_result:
            return jsonify(error=f"AI 分析失敗: {ai_result['error']}"), 500
        
        # 組合回應數據
        response_data = {
            'success': True,
            'ear_tag': ear_tag,
            'target_days': target_days,
            'predicted_weight': round(predicted_weight, 2),
            'average_daily_gain': round(average_daily_gain, 3),
            'pred_interval': {
                'q10': round(pred_interval['q10'], 2) if pred_interval['q10'] is not None else None,
                'q90': round(pred_interval['q90'], 2) if pred_interval['q90'] is not None else None
            },
            'prediction_source': prediction_source,
            'prediction_warning': prediction_warning,
            'current_age_months': current_age_months,
            'data_quality_report': data_quality_report,
            'breed_reference': {
                'breed': sheep.Breed,
                'min_gain': breed_ranges['min'],
                'max_gain': breed_ranges['max']
            },
            'historical_data_count': len(weight_data),
            'ai_analysis': ai_result.get('text', ''),
            'daily_forecasts': prediction_metrics.get('daily_forecasts'),
            'daily_confidence_band': prediction_metrics.get('daily_confidence_band'),
            'sheep_basic_info': {
                'ear_tag': sheep.EarNum,
                'breed': sheep.Breed,
                'sex': sheep.Sex,
                'birth_date': sheep.BirthDate
            },
            'model_applicability': {
                'scope': 'juvenile_only',
                'min_age_days': MIN_ELIGIBLE_AGE_DAYS,
                'max_age_days': MAX_ELIGIBLE_AGE_DAYS,
                'current_age_days': current_days,
                'target_future_age_days': current_days + target_days,
                'allows_future_age_extrapolation': True
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"預測API錯誤: {e}", exc_info=True)
        return jsonify(error=f"系統錯誤: {str(e)}"), 500

@bp.route('/goats/<string:ear_tag>/prediction/chart-data', methods=['GET'])
@login_required
def get_prediction_chart_data(ear_tag):
    """獲取預測圖表數據"""
    try:
        target_days = request.args.get('target_days', 30, type=int)
        
        api_key = request.headers.get('X-Api-Key')
        if not api_key:
            return jsonify(error="未提供API金鑰於請求頭中 (X-Api-Key)"), 401
        
        # 獲取羊隻資料
        sheep = Sheep.query.filter_by(user_id=current_user.id, EarNum=ear_tag).first()
        if not sheep:
            return jsonify(error=f"找不到耳號為 {ear_tag} 的羊隻"), 404
        
        # 獲取體重歷史記錄
        weight_records = SheepHistoricalData.query.filter_by(
            sheep_id=sheep.id,
            record_type='Body_Weight_kg'
        ).order_by(SheepHistoricalData.record_date.asc()).all()
        
        if len(weight_records) < 3:
            return jsonify(error="數據不足，至少需要3筆體重記錄"), 400
        
        birth_date, current_days, applicability_error = _validate_prediction_applicability(sheep, target_days)
        if applicability_error:
            return jsonify(error=applicability_error), 400

        # 準備圖表數據
        weight_data = [record.to_dict() for record in weight_records]
        prediction_metrics, error_message = _compute_prediction_metrics(sheep, weight_data, target_days, birth_date)
        if error_message:
            return jsonify(error=error_message), 400

        prediction_interval = {
            'q10': round(prediction_metrics['pred_interval']['q10'], 2) if prediction_metrics['pred_interval']['q10'] is not None else None,
            'q90': round(prediction_metrics['pred_interval']['q90'], 2) if prediction_metrics['pred_interval']['q90'] is not None else None
        }

        historical_points = []
        for record in weight_records:
            record_date = datetime.strptime(record.record_date, '%Y-%m-%d').date()
            weight = float(record.value)
            if birth_date:
                days_from_birth = (record_date - birth_date).days
                historical_points.append({
                    'x': days_from_birth,
                    'y': weight,
                    'date': record.record_date,
                    'label': f"{record.record_date} ({weight}kg)"
                })

        forecast_line = []
        for entry in prediction_metrics.get('daily_forecasts') or []:
            forecast_line.append({
                'x': entry['age_days'],
                'y': entry['predicted_weight'],
                'date': entry['date'],
                'day_offset': entry['day_offset']
            })

        confidence_band = []
        for entry in prediction_metrics.get('daily_confidence_band') or []:
            confidence_band.append({
                'x': entry['age_days'],
                'lower': entry['lower'],
                'upper': entry['upper'],
                'date': entry['date'],
                'day_offset': entry['day_offset']
            })

        prediction_point = None
        if forecast_line:
            last_point = forecast_line[-1]
            label_weight = last_point['y']
            label_text = f"預測 ({label_weight:.2f}kg)" if label_weight is not None else '預測'
            prediction_point = {
                'x': last_point['x'],
                'y': label_weight,
                'date': last_point.get('date'),
                'day_offset': last_point.get('day_offset'),
                'label': label_text
            }

        chart_data = {
            'historical_points': historical_points,
            'trend_line': forecast_line,
            'forecast_line': forecast_line,
            'confidence_band': confidence_band,
            'prediction_point': prediction_point,
            'prediction_source': prediction_metrics['prediction_source'],
            'prediction_interval': prediction_interval,
            'prediction_warning': prediction_metrics['prediction_warning']
        }

        return jsonify(chart_data)
        
    except Exception as e:
        current_app.logger.error(f"圖表數據API錯誤: {e}", exc_info=True)
        return jsonify(error=f"系統錯誤: {str(e)}"), 500

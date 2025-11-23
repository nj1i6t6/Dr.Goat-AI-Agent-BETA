from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from datetime import datetime
import hashlib
import hmac
from sqlalchemy.ext.declarative import declared_attr

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    sheep = db.relationship('Sheep', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    events = db.relationship('SheepEvent', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    chat_history = db.relationship('ChatHistory', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    event_type_options = db.relationship('EventTypeOption', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    event_description_options = db.relationship('EventDescriptionOption', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    product_batches = db.relationship('ProductBatch', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    iot_devices = db.relationship('IotDevice', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    automation_rules = db.relationship('AutomationRule', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    cost_entries = db.relationship('CostEntry', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    revenue_entries = db.relationship('RevenueEntry', backref='owner', lazy='dynamic', cascade="all, delete-orphan")


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class EventTypeOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    
    descriptions = db.relationship('EventDescriptionOption', backref='event_type', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_default': self.is_default,
            'descriptions': [d.to_dict() for d in self.descriptions]
        }

class EventDescriptionOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_type_option_id = db.Column(db.Integer, db.ForeignKey('event_type_option.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'event_type_option_id': self.event_type_option_id,
            'description': self.description,
            'is_default': self.is_default
        }

class Sheep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # --- 核心基础识别资料 (Core Identification) ---
    EarNum = db.Column(db.String(100), nullable=False) # 耳号
    BirthDate = db.Column(db.String(50)) # 出生日期
    Sex = db.Column(db.String(20)) # 性别
    Breed = db.Column(db.String(100)) # 品种
    
    # --- 血统资料 (Pedigree) ---
    Sire = db.Column(db.String(100)) # 父号
    Dam = db.Column(db.String(100)) # 母号
    
    # --- 根据 Excel _Basic 工作表扩充的栏位 ---
    BirWei = db.Column(db.Float) # 出生体重 (Birth Weight)
    SireBre = db.Column(db.String(100)) # 父系品种 (Sire's Breed)
    DamBre = db.Column(db.String(100)) # 母系品种 (Dam's Breed)
    MoveCau = db.Column(db.String(100)) # 异动原因 (Move Cause)
    MoveDate = db.Column(db.String(50)) # 异动日期 (Move Date)
    Class = db.Column(db.String(100)) # 等级/分类
    LittleSize = db.Column(db.Integer) # 产仔数/窝数 (Litter Size)
    Lactation = db.Column(db.Integer) # 泌乳胎次
    ManaClas = db.Column(db.String(100)) # 管理分类 (Management Class)
    FarmNum = db.Column(db.String(100)) # 牧场编号
    RUni = db.Column(db.String(100)) # 唯一记录编号

    # --- 饲养管理与生产性能资料 (Management & Performance) ---
    Body_Weight_kg = db.Column(db.Float) # 体重
    Age_Months = db.Column(db.Integer) # 月龄
    breed_category = db.Column(db.String(50)) # 品种类别 (乳、肉、毛)
    status = db.Column(db.String(100)) # 生理状态
    status_description = db.Column(db.Text) # 其他生理状态描述
    target_average_daily_gain_g = db.Column(db.Float) # 目标日增重
    milk_yield_kg_day = db.Column(db.Float) # 日产奶量
    milk_fat_percentage = db.Column(db.Float) # 乳脂率
    number_of_fetuses = db.Column(db.Integer) # 怀胎数
    expected_fiber_yield_g_day = db.Column(db.Float) # 预计产毛量
    activity_level = db.Column(db.String(100)) # 活动量
    
    # --- 备注与提醒 (Notes & Reminders) ---
    other_remarks = db.Column(db.Text) # 使用者备注
    agent_notes = db.Column(db.Text) # AI代理人备注
    next_vaccination_due_date = db.Column(db.String(50)) # 下次疫苗日期
    next_deworming_due_date = db.Column(db.String(50)) # 下次驱虫日期
    expected_lambing_date = db.Column(db.String(50)) # 预计产仔日期
    
    # --- ESG 相關欄位 ---
    manure_management = db.Column(db.String(100)) # 糞肥管理方式 (例如：堆肥、厭氧發酵)
    primary_forage_type = db.Column(db.String(100)) # 主要草料類型 (例如：在地狼尾草、進口苜蓿草)
    welfare_score = db.Column(db.Integer) # 動物福利評分 (1-5分)

    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'EarNum', name='_user_ear_num_uc'),
        db.Index('ix_sheep_user_status', 'user_id', 'status'),
    )
    
    historical_data = db.relationship('SheepHistoricalData', backref='sheep', lazy='dynamic', cascade="all, delete-orphan")
    batch_links = db.relationship('BatchSheepAssociation', back_populates='sheep', cascade="all, delete-orphan", overlaps='product_batches,sheep_links')
    product_batches = db.relationship('ProductBatch', secondary='batch_sheep_association', back_populates='sheep', lazy='dynamic', overlaps='batch_links,sheep_links')
    cost_entries = db.relationship('CostEntry', backref='sheep', lazy='dynamic', cascade="all, delete-orphan")
    revenue_entries = db.relationship('RevenueEntry', backref='sheep', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f'<Sheep {self.EarNum} OwnerID:{self.user_id}>'

class SheepEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sheep_id = db.Column(db.Integer, db.ForeignKey('sheep.id', ondelete='CASCADE'), nullable=False)

    event_date = db.Column(db.String(50), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # --- ESG - 食品安全相關欄位 ---
    medication = db.Column(db.String(150)) # 用藥名稱
    withdrawal_days = db.Column(db.Integer) # 停藥天數

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sheep = db.relationship('Sheep', backref=db.backref('events', lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        db.Index('ix_sheep_event_user_sheep_date', 'user_id', 'sheep_id', 'event_date'),
        db.Index('ix_sheep_event_user_type_date', 'user_id', 'event_type', 'event_date'),
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f'<Event {self.event_type} for SheepID:{self.sheep_id}>'
        
class SheepHistoricalData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sheep_id = db.Column(db.Integer, db.ForeignKey('sheep.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    record_date = db.Column(db.String(50), nullable=False)
    record_type = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_sheep_hist_user_type_date', 'user_id', 'record_type', 'record_date'),
    )
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f'<HistoricalData {self.record_type}:{self.value} for SheepID:{self.sheep_id}>'


class FinanceEntryMixin:
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    sheep_id = db.Column(db.Integer, db.ForeignKey('sheep.id', ondelete='SET NULL'))

    recorded_at = db.Column(db.DateTime, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100))
    label = db.Column(db.String(150))
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(8), default='TWD')

    breed = db.Column(db.String(100))
    age_months = db.Column(db.Integer)
    lactation_number = db.Column(db.Integer)
    production_stage = db.Column(db.String(100))

    notes = db.Column(db.Text)
    extra_metadata = db.Column(db.JSON, default=dict)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    @declared_attr
    def __table_args__(cls):  # type: ignore[override]
        base_name = cls.__tablename__
        return (
            db.Index(f'ix_{base_name}_user_recorded', 'user_id', 'recorded_at'),
            db.Index(f'ix_{base_name}_user_category', 'user_id', 'category'),
            db.Index(f'ix_{base_name}_user_breed', 'user_id', 'breed'),
        )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class CostEntry(FinanceEntryMixin, db.Model):
    pass


class RevenueEntry(FinanceEntryMixin, db.Model):
    pass


class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ear_num_context = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Chat {self.session_id} - {self.role}>'


class VerifiableLog(db.Model):
    __tablename__ = 'verifiable_log'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    event_data = db.Column(db.JSON, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    previous_hash = db.Column(db.String(64))
    current_hash = db.Column(db.String(64), nullable=False)

    __table_args__ = (
        db.Index('ix_verifiable_log_entity', 'entity_type', 'entity_id', 'id'),
        db.Index('ix_verifiable_log_current_hash', 'current_hash', unique=True),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'event_data': self.event_data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'previous_hash': self.previous_hash,
            'current_hash': self.current_hash,
        }


class ProductBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    batch_number = db.Column(db.String(100), nullable=False, unique=True, index=True)
    product_name = db.Column(db.String(150), nullable=False)
    product_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    esg_highlights = db.Column(db.Text)
    production_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date)
    origin_story = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps = db.relationship('ProcessingStep', order_by='ProcessingStep.sequence_order', back_populates='batch', cascade="all, delete-orphan")
    sheep_links = db.relationship('BatchSheepAssociation', back_populates='batch', cascade="all, delete-orphan", overlaps='sheep,product_batches,batch_links')
    sheep = db.relationship('Sheep', secondary='batch_sheep_association', back_populates='product_batches', overlaps='sheep_links,batch_links')

    def to_dict(self, include_relationships=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'batch_number': self.batch_number,
            'product_name': self.product_name,
            'product_type': self.product_type,
            'description': self.description,
            'esg_highlights': self.esg_highlights,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'origin_story': self.origin_story,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relationships:
            data['steps'] = [step.to_dict() for step in self.steps]
            data['sheep_links'] = [link.to_dict(include_sheep=True) for link in self.sheep_links]
        return data

    def __repr__(self):
        return f'<ProductBatch {self.batch_number} OwnerID:{self.user_id}>'


class ProcessingStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('product_batch.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    sequence_order = db.Column(db.Integer, nullable=False, default=1)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    evidence_url = db.Column(db.String(255))

    batch = db.relationship('ProductBatch', back_populates='steps')

    __table_args__ = (
        db.Index('ix_processing_step_batch_order', 'batch_id', 'sequence_order'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'title': self.title,
            'description': self.description,
            'sequence_order': self.sequence_order,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'evidence_url': self.evidence_url,
        }

    def __repr__(self):
        return f'<ProcessingStep {self.title} BatchID:{self.batch_id}>'


class BatchSheepAssociation(db.Model):
    __tablename__ = 'batch_sheep_association'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('product_batch.id', ondelete='CASCADE'), nullable=False)
    sheep_id = db.Column(db.Integer, db.ForeignKey('sheep.id', ondelete='CASCADE'), nullable=False)
    contribution_type = db.Column(db.String(100))
    quantity = db.Column(db.Float)
    quantity_unit = db.Column(db.String(50))
    role = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    batch = db.relationship('ProductBatch', back_populates='sheep_links', overlaps='sheep,product_batches')
    sheep = db.relationship('Sheep', back_populates='batch_links', overlaps='product_batches,sheep_links,batch_links,sheep')

    __table_args__ = (
        db.UniqueConstraint('batch_id', 'sheep_id', name='uq_batch_sheep'),
    )

    __mapper_args__ = {
        'confirm_deleted_rows': False
    }

    def to_dict(self, include_sheep=False):
        data = {
            'id': self.id,
            'batch_id': self.batch_id,
            'sheep_id': self.sheep_id,
            'contribution_type': self.contribution_type,
            'quantity': self.quantity,
            'quantity_unit': self.quantity_unit,
            'role': self.role,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_sheep and self.sheep:
            data['sheep'] = self.sheep.to_dict()
        return data

    def __repr__(self):
        return f'<BatchSheepAssociation BatchID:{self.batch_id} SheepID:{self.sheep_id}>'


def _get_api_hmac_secret() -> bytes:
    secret = current_app.config.get('API_HMAC_SECRET')
    if not secret:
        raise RuntimeError('API_HMAC_SECRET 未設定，無法處理 IoT 金鑰')
    if isinstance(secret, str):
        return secret.encode('utf-8')
    return secret


class IotDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    device_type = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(120))
    control_url = db.Column(db.String(255))
    status = db.Column(db.String(32), default='offline', nullable=False)
    last_seen = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    api_key_digest = db.Column(db.String(64), unique=True, index=True, nullable=False)

    sensor_readings = db.relationship(
        'SensorReading',
        backref='device',
        lazy='dynamic',
        cascade="all, delete-orphan"
    )
    trigger_rules = db.relationship(
        'AutomationRule',
        foreign_keys='AutomationRule.trigger_source_device_id',
        backref='trigger_device',
        lazy='dynamic'
    )
    target_rules = db.relationship(
        'AutomationRule',
        foreign_keys='AutomationRule.action_target_device_id',
        backref='target_device',
        lazy='dynamic'
    )
    control_logs = db.relationship(
        'DeviceControlLog',
        foreign_keys='DeviceControlLog.target_device_id',
        backref='target_device',
        lazy='dynamic'
    )

    __table_args__ = (
        db.Index('ix_iot_device_user_category', 'user_id', 'category'),
    )

    @staticmethod
    def compute_digest(raw_key: str) -> str:
        secret = _get_api_hmac_secret()
        return hmac.new(secret, raw_key.encode('utf-8'), hashlib.sha256).hexdigest()

    def set_api_key(self, raw_key: str) -> None:
        self.api_key_digest = self.compute_digest(raw_key)

    def verify_api_key(self, candidate: str) -> bool:
        if not candidate:
            return False
        candidate_digest = self.compute_digest(candidate)
        return hmac.compare_digest(candidate_digest, self.api_key_digest)

    def mark_seen(self) -> None:
        self.last_seen = datetime.utcnow()
        self.status = 'online'

    def to_safe_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'category': self.category,
            'location': self.location,
            'control_url': self.control_url,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<IotDevice {self.name} ({self.category})>'


class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('iot_device.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index('ix_sensor_reading_device_created_at', 'device_id', 'created_at'),
    )

    def __repr__(self):
        return f'<SensorReading device={self.device_id} at {self.created_at}>'


class AutomationRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    trigger_source_device_id = db.Column(db.Integer, db.ForeignKey('iot_device.id'), nullable=False)
    trigger_condition = db.Column(db.JSON, nullable=False)
    action_target_device_id = db.Column(db.Integer, db.ForeignKey('iot_device.id'), nullable=False)
    action_command = db.Column(db.JSON, nullable=False)
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    control_logs = db.relationship(
        'DeviceControlLog',
        backref='rule',
        lazy='dynamic',
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<AutomationRule {self.name} enabled={self.is_enabled}>'


class DeviceControlLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('automation_rule.id'), nullable=False)
    target_device_id = db.Column(db.Integer, db.ForeignKey('iot_device.id'), nullable=False)
    command = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(32), default='pending', nullable=False)
    response_payload = db.Column(db.JSON)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index('ix_device_control_log_rule', 'rule_id', 'executed_at'),
    )

    def __repr__(self):
        return f'<DeviceControlLog rule={self.rule_id} device={self.target_device_id}>'
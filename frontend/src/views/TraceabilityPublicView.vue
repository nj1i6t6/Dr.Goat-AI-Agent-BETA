<template>
  <div class="trace-public-page" v-loading="loading">
    <header class="public-header">
      <h1>產品產銷履歷</h1>
      <p class="subtitle">此頁面僅提供已公開的批次資訊，無需登入即可瀏覽。</p>
    </header>

    <el-empty
      v-if="!loading && errorMessage"
      :description="errorMessage"
    >
      <template #extra>
        <el-button type="primary" @click="retryFetch">重新嘗試</el-button>
      </template>
    </el-empty>

    <template v-else-if="story">
      <el-card class="batch-card" shadow="never">
        <template #header>
          <div class="card-header">
            <div>
              <h2 class="batch-title">{{ story.batch.product_name }}</h2>
              <p class="batch-number">批次號：{{ story.batch.batch_number }}</p>
            </div>
            <el-tag type="success" effect="dark" v-if="story.batch.is_public">對外公開中</el-tag>
          </div>
        </template>
        <div class="batch-meta">
          <div class="meta-item">
            <span class="label">產品類型</span>
            <span class="value">{{ story.batch.product_type || '未提供' }}</span>
          </div>
          <div class="meta-item">
            <span class="label">生產日期</span>
            <span class="value">{{ formatDate(story.batch.production_date) }}</span>
          </div>
          <div class="meta-item">
            <span class="label">建議賞味期限</span>
            <span class="value">{{ formatDate(story.batch.expiration_date) }}</span>
          </div>
        </div>
        <div class="batch-description" v-if="story.batch.description">
          <h4>產品簡介</h4>
          <p>{{ story.batch.description }}</p>
        </div>
        <div class="batch-description" v-if="story.batch.esg_highlights">
          <h4>ESG 亮點</h4>
          <el-alert :title="story.batch.esg_highlights" type="success" show-icon></el-alert>
        </div>
        <div class="batch-description" v-if="story.batch.origin_story">
          <h4>品牌故事</h4>
          <p>{{ story.batch.origin_story }}</p>
        </div>
      </el-card>

      <el-row :gutter="24" class="info-row">
        <el-col :md="12" :xs="24">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <h3>加工歷程</h3>
              </div>
            </template>
            <el-timeline>
              <el-timeline-item
                v-for="step in story.processing_timeline"
                :key="step.title + step.sequence_order"
                :timestamp="formatTimeline(step)"
                placement="top"
              >
                <div class="timeline-item">
                  <div class="timeline-header">
                    <h4>{{ step.sequence_order ? `Step ${step.sequence_order}` : '步驟' }}</h4>
                    <el-button
                      class="fingerprint-button"
                      link
                      :type="step.fingerprints?.length ? 'primary' : 'info'"
                      :disabled="!step.fingerprints?.length"
                      @click="openFingerprint(step)"
                    >
                      <svg class="fingerprint-icon" viewBox="0 0 24 24" aria-hidden="true">
                        <path
                          fill="currentColor"
                          d="M12 2l7 3v6c0 5.2-3.7 9.8-7 11-3.3-1.2-7-5.8-7-11V5l7-3zm0 2.18L7 5.9v5.1c0 3.6 2.5 7.3 5 8.6 2.5-1.3 5-5 5-8.6V5.9l-5-1.72zm-1 8.39l-2-2 1.41-1.41L11 9.76l2.59-2.59L15 8.59l-4 3.98z"
                        />
                      </svg>
                      <span>數據指紋</span>
                    </el-button>
                  </div>
                  <p class="timeline-title">{{ step.title }}</p>
                  <p class="timeline-desc" v-if="step.description">{{ step.description }}</p>
                  <div class="timeline-actions">
                    <el-link v-if="step.evidence_url" :href="step.evidence_url" target="_blank" type="primary">
                      查看佐證資料
                    </el-link>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-if="!story.processing_timeline.length" description="尚未建立加工流程" />
          </el-card>
        </el-col>
        <el-col :md="12" :xs="24">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <h3>參與羊隻</h3>
              </div>
            </template>
            <el-empty v-if="!story.sheep_details.length" description="尚未關聯羊隻" />
            <el-collapse v-else accordion>
              <el-collapse-item
                v-for="detail in story.sheep_details"
                :key="detail.link.id"
                :title="formatSheepTitle(detail)"
              >
                <div class="sheep-section">
                  <h4>基本資料</h4>
                  <div class="grid">
                    <div class="grid-item"><span>耳號</span><strong>{{ detail.sheep.EarNum }}</strong></div>
                    <div class="grid-item"><span>品種</span><strong>{{ detail.sheep.Breed || '未提供' }}</strong></div>
                    <div class="grid-item"><span>性別</span><strong>{{ detail.sheep.Sex || '未提供' }}</strong></div>
                    <div class="grid-item"><span>牧場編號</span><strong>{{ detail.sheep.FarmNum || '未提供' }}</strong></div>
                  </div>
                  <div class="section-block" v-if="detail.link.notes">
                    <h5>角色備註</h5>
                    <p>{{ detail.link.notes }}</p>
                  </div>
                  <div class="section-block" v-if="detail.recent_events.length">
                    <h5>重要事件</h5>
                    <ul class="bullet-list">
                      <li v-for="event in detail.recent_events" :key="event.id">
                        <strong>{{ event.event_date }}</strong>｜{{ event.event_type }}
                        <span v-if="event.description"> - {{ event.description }}</span>
                        <el-tag v-if="event.medication" type="warning" size="small">用藥：{{ event.medication }}</el-tag>
                      </li>
                    </ul>
                  </div>
                  <div class="section-block" v-if="detail.recent_history.length">
                    <h5>歷史數據</h5>
                    <ul class="bullet-list">
                      <li v-for="record in detail.recent_history" :key="record.id">
                        {{ record.record_date }}｜{{ record.record_type }}：{{ record.value }}
                        <span v-if="record.notes">（{{ record.notes }}）</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>

  <el-dialog
    v-model="fingerprintModal.visible"
    :title="`數據指紋 - ${fingerprintModal.stepTitle || '未命名步驟'}`"
    width="720px"
    class="fingerprint-dialog"
  >
    <template v-if="fingerprintModal.entries.length">
      <div class="fingerprint-actions">
        <el-button @click="copyFingerprint">複製 JSON</el-button>
        <el-button type="primary" @click="downloadFingerprint">下載 JSON</el-button>
      </div>
      <el-timeline>
        <el-timeline-item
          v-for="entry in fingerprintModal.entries"
          :key="entry.id"
          :timestamp="formatFingerprintTimestamp(entry.timestamp)"
          placement="top"
        >
          <div class="fingerprint-entry">
            <div class="fingerprint-entry-header">
              <el-tag size="small">{{ entry.event_data?.action || 'event' }}</el-tag>
              <strong>{{ entry.event_data?.summary || '未提供摘要' }}</strong>
            </div>
            <p class="fingerprint-actor" v-if="entry.event_data?.actor?.username">
              操作人員：{{ entry.event_data.actor.username }}
            </p>
            <p class="fingerprint-hash">
              <span>前一筆 Hash：</span><code>{{ entry.previous_hash || '—' }}</code>
            </p>
            <p class="fingerprint-hash">
              <span>目前 Hash：</span><code>{{ entry.current_hash }}</code>
            </p>
            <div class="fingerprint-metadata">
              <h5>Metadata</h5>
              <pre>{{ formatMetadata(entry.event_data?.metadata) }}</pre>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </template>
    <el-empty v-else description="尚無可驗證紀錄" />
  </el-dialog>
</template>

<script setup>
import { onMounted, ref, computed, reactive } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api';

const route = useRoute();
const batchNumber = computed(() => route.params.batchNumber);
const loading = ref(false);
const story = ref(null);
const errorMessage = ref('');
const fingerprintModal = reactive({
  visible: false,
  stepTitle: '',
  entries: [],
});

const fetchStory = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    story.value = await api.getPublicTraceBatch(batchNumber.value);
  } catch (error) {
    errorMessage.value = error?.error || error?.message || '載入產銷履歷失敗';
    ElMessage.error(errorMessage.value);
  } finally {
    loading.value = false;
  }
};

const retryFetch = () => fetchStory();

const formatDate = (value) => {
  if (!value) return '未提供';
  try {
    return new Date(value).toLocaleDateString();
  } catch (error) {
    return value;
  }
};

const formatTimeline = (step) => {
  const started = step.started_at ? new Date(step.started_at).toLocaleString() : null;
  const completed = step.completed_at ? new Date(step.completed_at).toLocaleString() : null;
  if (started && completed) {
    return `${started} ~ ${completed}`;
  }
  return started || completed || '';
};

const formatSheepTitle = (detail) => {
  const sheep = detail.sheep || {};
  const roleText = detail.link.role || detail.link.contribution_type || '參與';
  return `${sheep.EarNum || '未知耳號'}｜${roleText}`;
};

const openFingerprint = (step) => {
  fingerprintModal.visible = true;
  fingerprintModal.stepTitle = step.title || `Step ${step.sequence_order || ''}`;
  fingerprintModal.entries = Array.isArray(step.fingerprints) ? [...step.fingerprints] : [];
};

const formatFingerprintTimestamp = (value) => {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString();
  } catch (error) {
    return value;
  }
};

const formatMetadata = (metadata) => {
  if (!metadata || Object.keys(metadata).length === 0) {
    return '—';
  }
  try {
    return JSON.stringify(metadata, null, 2);
  } catch (error) {
    return String(metadata);
  }
};

const buildFingerprintPayload = () => ({
  stepTitle: fingerprintModal.stepTitle,
  entries: fingerprintModal.entries,
});

const copyFingerprint = async () => {
  const payloadText = JSON.stringify(buildFingerprintPayload(), null, 2);
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(payloadText);
      ElMessage.success('已複製數據指紋');
    } else {
      throw new Error('Clipboard not available');
    }
  } catch (error) {
    ElMessage.error('無法自動複製，請手動複製 JSON 內容');
  }
};

const downloadFingerprint = () => {
  try {
    const blob = new Blob([JSON.stringify(buildFingerprintPayload(), null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    const safeTitle = fingerprintModal.stepTitle.replace(/[^\w\-]+/g, '_');
    anchor.href = url;
    anchor.download = `fingerprint_${safeTitle || 'step'}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  } catch (error) {
    ElMessage.error('下載檔案時發生錯誤');
  }
};

onMounted(fetchStory);
</script>

<style scoped>
.trace-public-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 30px 20px 60px;
  min-height: 100vh;
}

.public-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.public-header h1 {
  margin: 0;
  font-size: 2rem;
  color: #1f2937;
  font-weight: 700;
}

.public-header .subtitle {
  margin: 0;
  color: #64748b;
}

.batch-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-title {
  margin: 0;
  font-size: 1.8rem;
  color: #1e3a8a;
}

.batch-number {
  margin: 4px 0 0;
  color: #64748b;
}

.batch-meta {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.meta-item {
  background: #f8fafc;
  border-radius: 12px;
  padding: 12px;
}

.meta-item .label {
  display: block;
  color: #64748b;
  font-size: 0.85rem;
}

.meta-item .value {
  font-weight: 600;
  color: #1f2937;
}

.batch-description {
  margin-top: 20px;
}

.batch-description h4 {
  margin-bottom: 8px;
  color: #1e293b;
}

.info-row {
  margin-top: 30px;
}

.timeline-item {
  padding-bottom: 12px;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.fingerprint-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.fingerprint-button[disabled] {
  color: var(--el-color-info-light-5, #cbd5f5);
}

.fingerprint-icon {
  width: 18px;
  height: 18px;
}

.timeline-actions {
  margin-top: 8px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.timeline-title {
  font-size: 1.1rem;
  color: #0f172a;
  margin: 4px 0;
}

.timeline-desc {
  color: #4b5563;
}

.sheep-section {
  padding: 10px 4px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: 15px;
}

.grid-item {
  background: #f1f5f9;
  border-radius: 10px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.grid-item span {
  font-size: 0.75rem;
  color: #64748b;
}

.grid-item strong {
  color: #0f172a;
}

.fingerprint-dialog .fingerprint-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 12px;
}

.fingerprint-entry {
  border: 1px solid var(--el-border-color-light, #dfe5f2);
  border-radius: 8px;
  padding: 12px;
  background: #f8fafc;
}

.fingerprint-entry + .fingerprint-entry {
  margin-top: 12px;
}

.fingerprint-entry-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.fingerprint-actor {
  font-size: 0.85rem;
  color: var(--el-text-color-secondary, #6b7280);
  margin: 0 0 6px;
}

.fingerprint-hash {
  font-family: var(--el-font-family-monospace, 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace);
  font-size: 0.85rem;
  margin: 4px 0;
  word-break: break-all;
}

.fingerprint-hash span {
  color: var(--el-text-color-secondary, #64748b);
  margin-right: 4px;
}

.fingerprint-metadata h5 {
  margin: 10px 0 4px;
  font-size: 0.9rem;
  color: #1e293b;
}

.fingerprint-metadata pre {
  background: rgba(15, 23, 42, 0.05);
  border-radius: 6px;
  padding: 8px;
  font-family: var(--el-font-family-monospace, 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace);
  font-size: 0.8rem;
  line-height: 1.45;
  max-height: 200px;
  overflow: auto;
}

.section-block {
  margin-bottom: 18px;
}

.section-block h5 {
  margin-bottom: 6px;
  color: #1e3a8a;
}

.bullet-list {
  margin: 0;
  padding-left: 18px;
  color: #334155;
}

.bullet-list li {
  margin-bottom: 6px;
}

@media (max-width: 768px) {
  .trace-public-page {
    padding: 20px 12px 40px;
  }

  .batch-title {
    font-size: 1.5rem;
  }

  .info-row {
    margin-top: 20px;
  }
}
</style>

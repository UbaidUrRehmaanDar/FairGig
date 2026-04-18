<template>
  <div class="log-shift-page">
    <main class="log-main">
      <div class="page-header">
        <div>
          <h1>Log a Shift</h1>
          <p>Add your shift earnings and optionally upload a screenshot for verification.</p>
        </div>
        <NuxtLink to="/dashboard/worker" class="header-link">Back to Dashboard</NuxtLink>
      </div>

      <section class="form-card">
        <form class="shift-form" novalidate @submit.prevent="submit">
          <div class="form-grid">
            <div class="input-group">
              <label for="platform">Platform</label>
              <div class="input-with-icon">
                <span class="icon">directions_car</span>
                <select id="platform" v-model="form.platform" :aria-invalid="!!errors.platform">
                  <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
                </select>
              </div>
              <p v-if="errors.platform" class="field-error">{{ errors.platform }}</p>
            </div>

            <div class="input-group">
              <label for="shift-date">Shift Date</label>
              <div class="input-with-icon">
                <span class="icon">calendar_month</span>
                <input
                  id="shift-date"
                  v-model="form.shift_date"
                  type="date"
                  :aria-invalid="!!errors.shift_date"
                />
              </div>
              <p v-if="errors.shift_date" class="field-error">{{ errors.shift_date }}</p>
            </div>

            <div class="input-group">
              <label for="hours-worked">Hours Worked</label>
              <div class="input-with-icon">
                <span class="icon">schedule</span>
                <input
                  id="hours-worked"
                  v-model.number="form.hours_worked"
                  type="number"
                  min="0"
                  step="0.5"
                  :aria-invalid="!!errors.hours_worked"
                  placeholder="e.g. 8"
                />
              </div>
              <p v-if="errors.hours_worked" class="field-error">{{ errors.hours_worked }}</p>
            </div>

            <div class="input-group">
              <label for="gross-earned">Gross Earned (PKR)</label>
              <div class="input-with-icon">
                <span class="icon">payments</span>
                <input
                  id="gross-earned"
                  v-model.number="form.gross_earned"
                  type="number"
                  min="0"
                  step="1"
                  :aria-invalid="!!errors.gross_earned"
                  placeholder="e.g. 5000"
                />
              </div>
              <p v-if="errors.gross_earned" class="field-error">{{ errors.gross_earned }}</p>
            </div>

            <div class="input-group">
              <label for="platform-deductions">Platform Deductions (PKR)</label>
              <div class="input-with-icon">
                <span class="icon">remove_circle</span>
                <input
                  id="platform-deductions"
                  v-model.number="form.platform_deductions"
                  type="number"
                  min="0"
                  step="1"
                  :aria-invalid="!!errors.platform_deductions"
                  placeholder="e.g. 1000"
                />
              </div>
              <p v-if="errors.platform_deductions" class="field-error">
                {{ errors.platform_deductions }}
              </p>
            </div>

            <div class="input-group">
              <label for="net-received">Net Received (PKR)</label>
              <div class="input-with-icon">
                <span class="icon">account_balance_wallet</span>
                <input
                  id="net-received"
                  v-model.number="form.net_received"
                  type="number"
                  min="0"
                  step="1"
                  :aria-invalid="!!errors.net_received"
                  placeholder="e.g. 4000"
                />
              </div>
              <p v-if="errors.net_received" class="field-error">{{ errors.net_received }}</p>
            </div>
          </div>

          <div class="input-group">
            <label for="notes">Notes (optional)</label>
            <div class="input-with-icon textarea-wrap">
              <span class="icon">edit_note</span>
              <textarea id="notes" v-model.trim="form.notes" rows="3" placeholder="Add notes..." />
            </div>
          </div>

          <div class="input-group">
            <label for="pre-submit-screenshot">Earnings Screenshot (optional)</label>
            <div class="upload-row">
              <input
                id="pre-submit-screenshot"
                :key="fileInputKey"
                type="file"
                accept="image/*"
                @change="onFileChange"
              />
              <button
                v-if="selectedFile"
                type="button"
                class="ghost-btn"
                @click="clearSelectedFile"
              >
                Remove Image
              </button>
            </div>
            <p class="field-hint">
              If selected, this image will be uploaded automatically after the shift is logged.
            </p>
            <div v-if="screenshotPreviewUrl" class="preview-wrap">
              <img
                :src="screenshotPreviewUrl"
                class="preview-image"
                alt="Selected screenshot preview"
              />
            </div>
          </div>

          <p v-if="message" :class="['form-message', messageType]">{{ message }}</p>

          <div class="actions">
            <button
              type="submit"
              class="primary-button"
              :class="{ 'is-loading': isSubmitting }"
              :disabled="isSubmitting"
            >
              <span v-if="!isSubmitting">Log Shift</span>
              <span v-else>Saving...</span>
            </button>
          </div>
        </form>
      </section>
    </main>

    <div class="support-fab">
      <button type="button">
        <span class="icon">help_outline</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' as any })

import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useShiftsStore } from '../../stores/shifts'
import { useApi } from '../../composables/useApi'

const shiftsStore = useShiftsStore()
const { authFetch } = useApi()

const platforms = ['Careem', 'InDrive', 'Bykea', 'Foodpanda', 'Cheetay', 'Other']

const form = reactive({
  platform: 'Careem',
  shift_date: '',
  hours_worked: null as number | null,
  gross_earned: null as number | null,
  platform_deductions: 0 as number | null,
  net_received: null as number | null,
  notes: ''
})

const errors = reactive({
  platform: '',
  shift_date: '',
  hours_worked: '',
  gross_earned: '',
  platform_deductions: '',
  net_received: ''
})

const isSubmitting = ref(false)
const message = ref('')
const messageType = ref<'error' | 'success'>('success')

const selectedFile = ref<File | null>(null)
const screenshotPreviewUrl = ref<string | null>(null)
const fileInputKey = ref(0)

const clearSelectedFile = () => {
  selectedFile.value = null
  if (screenshotPreviewUrl.value) {
    URL.revokeObjectURL(screenshotPreviewUrl.value)
    screenshotPreviewUrl.value = null
  }
  fileInputKey.value += 1
}

onBeforeUnmount(() => {
  if (screenshotPreviewUrl.value) {
    URL.revokeObjectURL(screenshotPreviewUrl.value)
  }
})

onMounted(() => {
  try {
    const preferred = window.localStorage.getItem('fg_default_platform') || ''
    if (preferred && platforms.includes(preferred)) {
      form.platform = preferred
    }
  } catch {
    // ignore
  }
})

const validate = () => {
  errors.platform = ''
  errors.shift_date = ''
  errors.hours_worked = ''
  errors.gross_earned = ''
  errors.platform_deductions = ''
  errors.net_received = ''

  if (!form.platform) errors.platform = 'Platform is required.'
  if (!form.shift_date) errors.shift_date = 'Shift date is required.'
  if (form.hours_worked !== null && Number(form.hours_worked) < 0) {
    errors.hours_worked = 'Hours worked cannot be negative.'
  }
  if (form.gross_earned === null || Number(form.gross_earned) <= 0) {
    errors.gross_earned = 'Gross earned must be greater than 0.'
  }
  if (form.platform_deductions !== null && Number(form.platform_deductions) < 0) {
    errors.platform_deductions = 'Deductions cannot be negative.'
  }
  if (form.net_received === null || Number(form.net_received) < 0) {
    errors.net_received = 'Net received cannot be negative.'
  }
  if (
    form.gross_earned !== null &&
    form.net_received !== null &&
    Number(form.net_received) > Number(form.gross_earned)
  ) {
    errors.net_received = 'Net received cannot exceed gross earned.'
  }

  return !Object.values(errors).some(Boolean)
}

const submit = async () => {
  if (isSubmitting.value) return
  message.value = ''

  if (!validate()) return

  isSubmitting.value = true
  try {
    const payload = {
      platform: form.platform,
      shift_date: form.shift_date,
      hours_worked: form.hours_worked,
      gross_earned: Number(form.gross_earned),
      platform_deductions: Number(form.platform_deductions || 0),
      net_received: Number(form.net_received),
      notes: form.notes || null
    }

    const result: any = await shiftsStore.logShift(payload)
    const shiftId = String(result?.shift_id || '').trim()

    const shouldUploadNow = Boolean(shiftId && selectedFile.value)
    if (shouldUploadNow) {
      await uploadScreenshot(shiftId)
      if (messageType.value === 'success') {
        message.value = 'Shift logged and screenshot uploaded for verification.'
      }
      return
    }

    messageType.value = 'success'
    message.value = 'Shift logged successfully.'
  } catch (e: any) {
    messageType.value = 'error'
    message.value = e?.message || 'Failed to log shift.'
  } finally {
    isSubmitting.value = false
  }
}

const onFileChange = (e: Event) => {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] || null

  if (screenshotPreviewUrl.value) {
    URL.revokeObjectURL(screenshotPreviewUrl.value)
    screenshotPreviewUrl.value = null
  }

  if (selectedFile.value && selectedFile.value.type.startsWith('image/')) {
    screenshotPreviewUrl.value = URL.createObjectURL(selectedFile.value)
  }
}

const uploadScreenshot = async (shiftId: string) => {
  if (!selectedFile.value || !shiftId) return

  try {
    const fd = new FormData()
    fd.append('file', selectedFile.value)

    await authFetch(`/screenshots/upload/${shiftId}`, {
      method: 'POST',
      body: fd
    })

    messageType.value = 'success'
    message.value = 'Screenshot uploaded for verification.'
    clearSelectedFile()
  } catch (e: any) {
    messageType.value = 'error'
    message.value =
      `Shift logged, but screenshot upload failed: ${e?.message || 'Failed to upload screenshot.'}`
  }
}
</script>

<style scoped>
.log-shift-page {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
  padding: 2rem;
}
.log-main {
  max-width: 980px;
  margin: 0 auto;
  display: grid;
  gap: 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}
.page-header h1 {
  font-size: 2rem;
  font-weight: 800;
}
.page-header p {
  margin-top: 0.35rem;
  color: var(--fg-muted);
}
.header-link {
  text-decoration: none;
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  border-radius: 9999px;
  padding: 0.65rem 0.9rem;
  font-size: 0.86rem;
  font-weight: 700;
}

.form-card,
.upload-card {
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: var(--fg-shadow);
}
.shift-form {
  display: grid;
  gap: 1rem;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 0.85rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}
.input-group label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--fg-muted);
  margin-left: 0.2rem;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}
.input-with-icon .icon {
  position: absolute;
  left: 0.85rem;
  color: var(--fg-muted);
  font-size: 1.2rem;
  pointer-events: none;
}
.input-with-icon input,
.input-with-icon select,
.input-with-icon textarea {
  width: 100%;
  border: none;
  border-radius: 1rem;
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  outline: none;
  font-family: inherit;
  padding: 0.9rem 1rem 0.9rem 2.75rem;
}
.input-with-icon textarea {
  resize: vertical;
}
.input-with-icon input:focus,
.input-with-icon select:focus,
.input-with-icon textarea:focus {
  background: var(--fg-surface);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-primary) 20%, transparent);
}
.input-with-icon input[aria-invalid='true'],
.input-with-icon select[aria-invalid='true'] {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--fg-danger) 20%, transparent);
  background: color-mix(in srgb, var(--fg-danger) 10%, var(--fg-surface));
}
.textarea-wrap .icon {
  top: 0.9rem;
}
.field-error {
  color: var(--fg-danger);
  font-size: 0.78rem;
  font-weight: 700;
  margin-left: 0.2rem;
}

.field-hint {
  color: var(--fg-muted);
  font-size: 0.78rem;
  font-weight: 600;
  margin-left: 0.2rem;
}

.preview-wrap {
  margin-top: 0.5rem;
  padding: 0.5rem;
  border: 1px solid var(--fg-border);
  border-radius: 0.75rem;
  background: var(--fg-surface-muted);
}

.preview-image {
  display: block;
  width: 100%;
  max-height: 260px;
  object-fit: contain;
  border-radius: 0.5rem;
}

.form-message {
  font-size: 0.84rem;
  font-weight: 700;
}
.form-message.success {
  color: var(--fg-success);
}
.form-message.error {
  color: var(--fg-danger);
}

.actions {
  display: flex;
  justify-content: center;
  padding-top: 0.4rem;
}
.primary-button {
  width: 18rem;
  height: 3.2rem;
  border: none;
  border-radius: 9999px;
  background: var(--fg-primary);
  color: #f2f1ff;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: var(--fg-shadow);
}
.primary-button.is-loading,
.primary-button:disabled {
  cursor: not-allowed;
  background: var(--fg-muted);
  box-shadow: var(--fg-shadow);
}

.upload-row {
  margin-top: 0.75rem;
  display: flex;
  gap: 0.7rem;
  flex-wrap: wrap;
  align-items: center;
}
.ghost-btn {
  border: none;
  border-radius: 9999px;
  background: var(--fg-surface-muted);
  color: var(--fg-text);
  font-weight: 700;
  padding: 0.55rem 0.9rem;
  cursor: pointer;
}
.ghost-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.support-fab {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 50;
}
.support-fab button {
  width: 3.5rem;
  height: 3.5rem;
  background: var(--fg-surface);
  border: 1px solid var(--fg-border);
  border-radius: 9999px;
  color: var(--fg-primary);
  box-shadow: var(--fg-shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

@media (min-width: 760px) {
  .form-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* Material Symbols Outlined */
.icon {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  direction: ltr;
  font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}
</style>
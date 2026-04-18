<template>
  <div class="new-grievance-page">
    <main class="new-main">
      <div class="page-header">
        <div>
          <h1>Post a Grievance</h1>
          <p>Share your issue clearly so advocates and verifiers can take action.</p>
        </div>
        <NuxtLink to="/grievances" class="header-link">Back to Board</NuxtLink>
      </div>

      <section class="form-card">
        <form class="grievance-form" novalidate @submit.prevent="submit">
          <div class="input-group">
            <label for="platform">Platform</label>
            <div class="input-with-icon">
              <span class="icon">business</span>
              <select id="platform" v-model="form.platform" :aria-invalid="!!errors.platform">
                <option disabled value="">Select platform</option>
                <option v-for="p in platforms" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
            <p v-if="errors.platform" class="field-error">{{ errors.platform }}</p>
          </div>

          <div class="input-group">
            <label for="category">Category</label>
            <div class="input-with-icon">
              <span class="icon">category</span>
              <select id="category" v-model="form.category" :aria-invalid="!!errors.category">
                <option disabled value="">Select category</option>
                <option value="commission_change">Commission Change</option>
                <option value="deactivation">Deactivation</option>
                <option value="payment_delay">Payment Delay</option>
                <option value="other">Other</option>
              </select>
            </div>
            <p v-if="errors.category" class="field-error">{{ errors.category }}</p>
          </div>

          <div class="input-group">
            <label for="title">Title</label>
            <div class="input-with-icon">
              <span class="icon">title</span>
              <input
                id="title"
                v-model.trim="form.title"
                type="text"
                :aria-invalid="!!errors.title"
                placeholder="e.g. Sudden commission increase this week"
              />
            </div>
            <p v-if="errors.title" class="field-error">{{ errors.title }}</p>
          </div>

          <div class="input-group">
            <label for="description">Description</label>
            <div class="input-with-icon textarea-wrap">
              <span class="icon">description</span>
              <textarea
                id="description"
                v-model.trim="form.description"
                rows="5"
                :aria-invalid="!!errors.description"
                placeholder="Explain what happened, when it happened, and expected resolution..."
              />
            </div>
            <p v-if="errors.description" class="field-error">{{ errors.description }}</p>
          </div>

          <div class="input-group">
            <label for="tags">Tags (comma separated, optional)</label>
            <div class="input-with-icon">
              <span class="icon">sell</span>
              <input id="tags" v-model.trim="tagsInput" type="text" placeholder="fare, payout, support" />
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
              <span v-if="!isSubmitting">Submit Grievance</span>
              <span v-else>Submitting...</span>
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

import { reactive, ref } from 'vue'
import { navigateTo } from 'nuxt/app'
import { useApi } from '../../composables/useApi'

const { authFetch } = useApi()

const platforms = ['Careem', 'InDrive', 'Bykea', 'Foodpanda', 'Cheetay', 'Other']

const form = reactive({
  platform: '',
  category: '',
  title: '',
  description: ''
})

const errors = reactive({
  platform: '',
  category: '',
  title: '',
  description: ''
})

const tagsInput = ref('')
const isSubmitting = ref(false)
const message = ref('')
const messageType = ref<'error' | 'success'>('success')

const validate = () => {
  errors.platform = ''
  errors.category = ''
  errors.title = ''
  errors.description = ''

  if (!form.platform) errors.platform = 'Platform is required.'
  if (!form.category) errors.category = 'Category is required.'
  if (!form.title) errors.title = 'Title is required.'
  if (form.title.length > 120) errors.title = 'Title should be under 120 characters.'
  if (!form.description) errors.description = 'Description is required.'
  if (form.description.length < 15) errors.description = 'Please provide more detail (min 15 chars).'

  return !Object.values(errors).some(Boolean)
}

const submit = async () => {
  if (isSubmitting.value) return
  message.value = ''

  if (!validate()) return

  const tags = tagsInput.value
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean)

  isSubmitting.value = true
  try {
    await authFetch('/grievances', {
      method: 'POST',
      body: {
        platform: form.platform,
        category: form.category,
        title: form.title,
        description: form.description,
        tags
      }
    })

    messageType.value = 'success'
    message.value = 'Grievance submitted successfully.'
    await navigateTo('/grievances')
  } catch (e: any) {
    messageType.value = 'error'
    message.value = e?.message || 'Failed to submit grievance.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.new-grievance-page {
  min-height: 100vh;
  background: #f5f7f9;
  color: #2c2f31;
  font-family: 'Raleway', sans-serif;
  padding: 2rem;
}
.new-main {
  max-width: 880px;
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
  color: #595c5e;
}
.header-link {
  text-decoration: none;
  background: #eef1f3;
  color: #2c2f31;
  border-radius: 9999px;
  padding: 0.65rem 0.9rem;
  font-size: 0.86rem;
  font-weight: 700;
}

.form-card {
  background: #ffffff;
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: 0 12px 24px -16px rgba(44, 47, 49, 0.18);
}
.grievance-form {
  display: grid;
  gap: 0.9rem;
}
.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}
.input-group label {
  font-size: 0.84rem;
  font-weight: 700;
  color: #595c5e;
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
  color: #abadaf;
  font-size: 1.2rem;
  pointer-events: none;
}
.input-with-icon input,
.input-with-icon select,
.input-with-icon textarea {
  width: 100%;
  border: none;
  border-radius: 1rem;
  background: #eef1f3;
  color: #2c2f31;
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
  background: #ffffff;
  box-shadow: 0 0 0 2px rgba(5, 69, 239, 0.2);
}
.input-with-icon input[aria-invalid='true'],
.input-with-icon select[aria-invalid='true'],
.input-with-icon textarea[aria-invalid='true'] {
  box-shadow: 0 0 0 2px rgba(217, 45, 32, 0.2);
  background: #fff6f6;
}
.textarea-wrap .icon {
  top: 0.9rem;
}

.field-error {
  color: #d92d20;
  font-size: 0.78rem;
  font-weight: 700;
  margin-left: 0.2rem;
}
.form-message {
  font-size: 0.84rem;
  font-weight: 700;
}
.form-message.success {
  color: #0b7a33;
}
.form-message.error {
  color: #d92d20;
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
  background: #0545ef;
  color: #f2f1ff;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: 0 12px 24px -8px rgba(5, 69, 239, 0.3);
}
.primary-button.is-loading,
.primary-button:disabled {
  cursor: not-allowed;
  background: #595c5e;
  box-shadow: 0 12px 18px -10px rgba(44, 47, 49, 0.25);
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
  border: none;
  border-radius: 9999px;
  background: #fff;
  color: #0545ef;
  box-shadow: 0 24px 24px -4px rgba(44, 47, 49, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
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
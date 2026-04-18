export const useGrievancesStore = () => {
  return {
    items: [] as any[],
    loading: false,
    async fetch() {
      return []
    },
    async create() {
      return { id: "skeleton-grievance-id" }
    },
    async upvote() {
      return { ok: true }
    },
    async escalate() {
      return { status: "escalated" }
    },
  }
}

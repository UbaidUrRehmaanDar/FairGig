export const useAnalyticsStore = () => {
  return {
    kpis: null as any,
    loading: false,
    async fetchKPIs() {
      return {
        commission_trends: [],
        income_by_zone: [],
        vulnerability_flags: [],
        top_complaints: [],
      }
    },
  }
}

export const useShiftsStore = () => {
  return {
    shifts: [] as any[],
    summary: null as any,
    cityMedian: null as any,
    loading: false,
    async fetchShifts() {
      return []
    },
    async fetchSummary() {
      return null
    },
    async logShift(_payload?: any) {
      return { shift_id: "skeleton-shift-id", status: "logged" }
    },
    async fetchCityMedian() {
      return null
    },
  }
}

export type FairGigRole = "worker" | "verifier" | "advocate"

export const useAuthStore = () => {
  // Placeholder shape preserved for later Pinia integration.
  return {
    user: null,
    role: "worker" as FairGigRole,
    async signUp() {
      return { status: "skeleton" }
    },
    async signIn() {
      return { status: "skeleton" }
    },
    async signOut() {
      return { status: "skeleton" }
    },
  }
}

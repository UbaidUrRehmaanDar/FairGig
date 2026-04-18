<template>
  <section>
    <h2>FairGig Skeleton</h2>
    <p>Starter structure generated from the project plan.</p>
    <div class="links">
      <NuxtLink to="/login">Login</NuxtLink>
      <NuxtLink to="/register">Register</NuxtLink>
      <NuxtLink to="/dashboard/worker">Worker Dashboard</NuxtLink>
      <NuxtLink to="/grievances">Grievance Board</NuxtLink>
      <NuxtLink to="/grievances"> Ref </NuxtLink>
    </div>
  </section>
</template>

<style scoped>
.links {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}
</style>

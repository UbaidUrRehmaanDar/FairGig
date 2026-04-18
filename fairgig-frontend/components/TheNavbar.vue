<template>
  <nav class="iphone-nav">
    <a href="#" class="nav-item active">
      <span class="material-symbols-outlined">home</span>
      <span class="text">Home</span>
    </a>
    <a href="#" class="nav-item">
      <span class="material-symbols-outlined">work</span>
      <span class="text">Shifts</span>
    </a>
    <a href="#" class="nav-item">
      <span class="material-symbols-outlined">description</span>
      <span class="text">Grievances</span>
    </a>
    <a href="#" class="nav-item">
      <span class="material-symbols-outlined">person</span>
      <span class="text">Profile</span>
    </a>
  </nav>
</template>

<style scoped>
.iphone-nav {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 2rem);
  max-width: 24rem;
  display: flex;
  justify-content: space-around;
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 2rem;
  padding: 0.75rem 0.5rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-decoration: none;
  color: #595c5e;
  transition: all 0.3s ease;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
}

.nav-item .icon {
  font-size: 1.75rem;
  margin-bottom: 0.125rem;
}

.nav-item .text {
  font-size: 0.75rem;
  font-weight: 600;
  font-family: 'Raleway', sans-serif;
}

.nav-item.active {
  color: #0545ef;
  background-color: rgba(5, 69, 239, 0.1);
}

.nav-item:not(.active):hover {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>

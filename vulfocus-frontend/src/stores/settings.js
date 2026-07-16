import { defineStore } from 'pinia'
import defaultSettings from '@/settings'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    showSettings: defaultSettings.showSettings || false,
    fixedHeader: defaultSettings.fixedHeader || true,
    sidebarLogo: defaultSettings.sidebarLogo || false,
  }),
  actions: {
    changeSetting({ key, value }) {
      if (this.hasOwnProperty(key)) {
        this[key] = value
      }
    },
  },
})

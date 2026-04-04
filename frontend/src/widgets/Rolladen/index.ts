import { WidgetRegistry } from '@/widgets/registry'
import Widget from './Widget.vue'
import Config from './Config.vue'

WidgetRegistry.register({
  type: 'Rolladen',
  label: 'Rolladen / Jalousie',
  icon: '🪟',
  minW: 3, minH: 3,
  defaultW: 4, defaultH: 4,
  component: Widget,
  configComponent: Config,
  defaultConfig: {
    label: '',
    mode: 'rolladen',        // 'rolladen' | 'jalousie'
    invert: false,           // true = 0% ist geschlossen, 100% ist offen
    invert_move_up: false,   // true = false ist aktiv (Hoch)
    invert_move_down: false, // true = false ist aktiv (Runter)
    dp_move_up: '',
    dp_move_down: '',
    dp_stop: '',
    dp_position: '',
    dp_position_status: '',
    dp_slat: '',
    dp_slat_status: '',
  },
  compatibleTypes: ['*'],
  noDatapoint: true,
  getExtraDatapointIds: (config) => {
    return [
      config.dp_position as string,
      config.dp_position_status as string,
      config.dp_slat as string,
      config.dp_slat_status as string,
    ].filter(Boolean) as string[]
  },
})

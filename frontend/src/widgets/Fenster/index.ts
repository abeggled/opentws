import { WidgetRegistry } from '@/widgets/registry'
import Widget from './Widget.vue'
import Config from './Config.vue'

WidgetRegistry.register({
  type: 'Fenster',
  label: 'Fenster / Türe',
  icon: '🚪',
  minW: 2, minH: 2,
  defaultW: 2, defaultH: 3,
  component: Widget,
  configComponent: Config,
  defaultConfig: {
    label: '',
    mode: 'fenster',        // 'fenster' | 'fenster_2' | 'tuere' | 'schiebetuer' | 'dachfenster'
    dp_contact: '',
    invert_contact: false,
    dp_tilt: '',
    invert_tilt: false,
    dp_contact_left: '',
    invert_contact_left: false,
    dp_tilt_left: '',
    invert_tilt_left: false,
    dp_contact_right: '',
    invert_contact_right: false,
    dp_tilt_right: '',
    invert_tilt_right: false,
    dp_position: '',
    handle_left:  true,
    handle_right: true,
  },
  compatibleTypes: ['*'],
  noDatapoint: true,
  getExtraDatapointIds: (config) => {
    return [
      config.dp_contact       as string,
      config.dp_tilt          as string,
      config.dp_contact_left  as string,
      config.dp_tilt_left     as string,
      config.dp_contact_right as string,
      config.dp_tilt_right    as string,
      config.dp_position      as string,
    ].filter(Boolean) as string[]
  },
})

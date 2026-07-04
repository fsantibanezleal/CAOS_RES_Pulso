// i18next setup (EN default per ADR-0011, ES translation). A tiny typed t() via react-i18next.
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { en } from './en';
import { es } from './es';

const saved = typeof localStorage !== 'undefined' ? localStorage.getItem('flowdna.lang') : null;

i18n.use(initReactI18next).init({
  resources: { en: { t: en }, es: { t: es } },
  lng: saved ?? 'en',
  fallbackLng: 'en',
  ns: ['t'],
  defaultNS: 't',
  interpolation: { escapeValue: false },
  returnObjects: true,
});

export default i18n;

// frontend/src/i18n/index.ts
/**
 * Internationalization (i18n) System for PsychSync
 * Multi-language support with React hooks
 * Dynamic language loading
 * RTL language support
 * Currency and number formatting
 * Date and time localization
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import en from './locales/en.json';
import es from './locales/es.json';
import fr from './locales/fr.json';
import de from './locales/de.json';
import ja from './locales/ja.json';
import zh from './locales/zh.json';

export type Language = 'en' | 'es' | 'fr' | 'de' | 'ja' | 'zh';

export interface TranslationKeys {
  // Common
  'common.yes': string;
  'common.no': string;
  'common.ok': string;
  'common.cancel': string;
  'common.save': string;
  'common.delete': string;
  'common.edit': string;
  'common.add': string;
  'common.search': string;
  'common.loading': string;
  'common.error': string;
  'common.success': string;
  'common.warning': string;
  'common.info': string;

  // Navigation
  'nav.dashboard': string;
  'nav.assessments': string;
  'nav.teams': string;
  'nav.settings': string;
  'nav.profile': string;
  'nav.logout': string;

  // Authentication
  'auth.login': string;
  'auth.register': string;
  'auth.forgot_password': string;
  'auth.reset_password': string;
  'auth.welcome_back': string;
  'auth.create_account': string;
  'auth.email': string;
  'auth.password': string;
  'auth.full_name': string;
  'auth.remember_me': string;

  // User
  'user.profile': string;
  'user.settings': string;
  'user.preferences': string;
  'user.notifications': string;
  'user.language': string;

  // Assessments
  'assessment.title': string;
  'assessment.description': string;
  'assessment.category': string;
  'assessment.status': string;
  'assessment.duration': string;
  'assessment.start': string;
  'assessment.complete': string;
  'assessment.results': string;
  'assessment.progress': string;

  // Teams
  'team.name': string;
  'team.members': string;
  'team.invite': string;
  'team.role': string;
  'team.admin': string;
  'team.member': string;

  // Errors
  'error.page_not_found': string;
  'error.server_error': string;
  'error.network_error': string;
  'error.validation_error': string;
  'error.unauthorized': string;
  'error.forbidden': string;

  // Success messages
  'success.saved': string;
  'success.deleted': string;
  'success.updated': string;
  'success.created': string;
  'success.completed': string;
  'success.uploaded': string;
}

export interface LanguageConfig {
  code: Language;
  name: string;
  nativeName: string;
  flag: string;
  rtl: boolean;
  dateFormat: string;
  numberFormat: {
    decimal: string;
    thousands: string;
  };
  currency: string;
}

// Language configurations
export const LANGUAGES: Record<Language, LanguageConfig> = {
  en: {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇺🇸',
    rtl: false,
    dateFormat: 'MM/DD/YYYY',
    numberFormat: {
      decimal: '.',
      thousands: ','
    },
    currency: 'USD'
  },
  es: {
    code: 'es',
    name: 'Spanish',
    nativeName: 'Español',
    flag: '🇪🇸',
    rtl: false,
    dateFormat: 'DD/MM/YYYY',
    numberFormat: {
      decimal: ',',
      thousands: '.'
    },
    currency: 'EUR'
  },
  fr: {
    code: 'fr',
    name: 'French',
    nativeName: 'Français',
    flag: '🇫🇷',
    rtl: false,
    dateFormat: 'DD/MM/YYYY',
    numberFormat: {
      decimal: ',',
      thousands: ' '
    },
    currency: 'EUR'
  },
  de: {
    code: 'de',
    name: 'German',
    nativeName: 'Deutsch',
    flag: '🇩🇪',
    rtl: false,
    dateFormat: 'DD.MM.YYYY',
    numberFormat: {
      decimal: ',',
      thousands: '.'
    },
    currency: 'EUR'
  },
  ja: {
    code: 'ja',
    name: 'Japanese',
    nativeName: '日本語',
    flag: '🇯🇵',
    rtl: false,
    dateFormat: 'YYYY/MM/DD',
    numberFormat: {
      decimal: '.',
      thousands: ','
    },
    currency: 'JPY'
  },
  zh: {
    code: 'zh',
    name: 'Chinese',
    nativeName: '中文',
    flag: '🇨🇳',
    rtl: false,
    dateFormat: 'YYYY-MM-DD',
    numberFormat: {
      decimal: '.',
      thousands: ','
    },
    currency: 'CNY'
  }
};

// Translation resources
export const TRANSLATIONS: Record<Language, Partial<TranslationKeys>> = {
  en,
  es,
  fr,
  de,
  ja,
  zh
} as any;

// Context type
interface I18nContextType {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  formatNumber: (number: number, options?: Intl.NumberFormatOptions) => string;
  formatDate: (date: Date | string, options?: Intl.DateTimeFormatOptions) => string;
  formatCurrency: (amount: number, currency?: string) => string;
  isRTL: boolean;
  availableLanguages: LanguageConfig[];
}

// Create context
const I18nContext = createContext<I18nContextType | undefined>(undefined);

// I18n Provider
interface I18nProviderProps {
  children: ReactNode;
  defaultLanguage?: Language;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({
  children,
  defaultLanguage = 'en'
}) => {
  const [language, setLanguageState] = useState<Language>(defaultLanguage);

  // Load language preference from localStorage
  useEffect(() => {
    const savedLanguage = localStorage.getItem('psychsync-language') as Language;
    if (savedLanguage && Object.values(LANGUAGES).some(lang => lang.code === savedLanguage)) {
      setLanguageState(savedLanguage);
    } else {
      // Detect browser language
      const browserLanguage = navigator.language.split('-')[0] as Language;
      if (Object.values(LANGUAGES).some(lang => lang.code === browserLanguage)) {
        setLanguageState(browserLanguage);
      }
    }
  }, []);

  // Save language preference to localStorage
  const setLanguage = (newLanguage: Language) => {
    setLanguageState(newLanguage);
    localStorage.setItem('psychsync-language', newLanguage);

    // Update HTML lang attribute
    document.documentElement.lang = newLanguage;

    // Update HTML dir attribute for RTL languages
    document.documentElement.dir = LANGUAGES[newLanguage].rtl ? 'rtl' : 'ltr';
  };

  // Translation function
  const t = (key: string, params?: Record<string, string | number>): string => {
    const keys = key.split('.');
    let value: any = TRANSLATIONS[language];

    // Navigate through nested keys
    for (const k of keys) {
      value = value?.[k];
    }

    if (typeof value !== 'string') {
      console.warn(`Translation key not found: ${key} for language: ${language}`);
      return key;
    }

    // Replace parameters
    if (params) {
      let result = value;
      Object.entries(params).forEach(([paramKey, paramValue]) => {
        result = result.replace(`{{${paramKey}}}`, String(paramValue));
      });
      return result;
    }

    return value;
  };

  // Number formatting
  const formatNumber = (
    number: number,
    options?: Intl.NumberFormatOptions
  ): string => {
    const languageConfig = LANGUAGES[language];
    const defaultOptions: Intl.NumberFormatOptions = {
      style: 'decimal',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
      ...options
    };

    try {
      return new Intl.NumberFormat(languageConfig.code, defaultOptions).format(number);
    } catch (error) {
      console.warn('Number formatting error:', error);
      return String(number);
    }
  };

  // Date formatting
  const formatDate = (
    date: Date | string,
    options?: Intl.DateTimeFormatOptions
  ): string => {
    const languageConfig = LANGUAGES[language];
    const dateObj = typeof date === 'string' ? new Date(date) : date;

    const defaultOptions: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      ...options
    };

    try {
      return new Intl.DateTimeFormat(languageConfig.code, defaultOptions).format(dateObj);
    } catch (error) {
      console.warn('Date formatting error:', error);
      return dateObj.toLocaleDateString();
    }
  };

  // Currency formatting
  const formatCurrency = (
    amount: number,
    currency?: string
  ): string => {
    const languageConfig = LANGUAGES[language];
    const currencyCode = currency || languageConfig.currency;

    try {
      return new Intl.NumberFormat(languageConfig.code, {
        style: 'currency',
        currency: currencyCode
      }).format(amount);
    } catch (error) {
      console.warn('Currency formatting error:', error);
      return `${currencyCode} ${amount.toFixed(2)}`;
    }
  };

  const isRTL = LANGUAGES[language].rtl;

  const value: I18nContextType = {
    language,
    setLanguage,
    t,
    formatNumber,
    formatDate,
    formatCurrency,
    isRTL,
    availableLanguages: Object.values(LANGUAGES)
  };

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
};

// Hook for using i18n
export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};

// Hook for translation
export const useTranslation = () => {
  const { t } = useI18n();
  return { t };
};

// Hook for language switching
export const useLanguage = () => {
  const { language, setLanguage, availableLanguages } = useI18n();

  const switchLanguage = (newLanguage: Language) => {
    if (Object.values(LANGUAGES).some(lang => lang.code === newLanguage)) {
      setLanguage(newLanguage);
    }
  };

  return {
    currentLanguage: language,
    switchLanguage,
    availableLanguages
  };
};

// Utility functions
export const getLanguageByCode = (code: string): LanguageConfig | undefined => {
  return Object.values(LANGUAGES).find(lang => lang.code === code);
};

export const isRTLLanguage = (language: Language): boolean => {
  return LANGUAGES[language].rtl;
};

export const formatDateForLanguage = (
  date: Date | string,
  language: Language,
  format?: Intl.DateTimeFormatOptions
): string => {
  const languageConfig = LANGUAGES[language];
  const dateObj = typeof date === 'string' ? new Date(date) : date;

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...format
  };

  try {
    return new Intl.DateTimeFormat(languageConfig.code, defaultOptions).format(dateObj);
  } catch (error) {
    console.warn('Date formatting error:', error);
    return dateObj.toLocaleDateString();
  }
};

// Pluralization helper
export const pluralize = (
  count: number,
  singular: string,
  plural?: string
): string => {
  if (count === 1) {
    return singular;
  }
  return plural || singular + 's';
};

// Format file size
export const formatFileSize = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

// Duration formatting
export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes > 0 ? `${minutes}m` : ''}${remainingSeconds > 0 ? `${remainingSeconds}s` : ''}`;
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds > 0 ? `${remainingSeconds}s` : ''}`;
  } else {
    return `${remainingSeconds}s`;
  }
};

export default I18nProvider;
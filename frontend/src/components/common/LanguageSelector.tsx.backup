import React, { useState, useEffect } from 'react';
import {
  Globe,
  ChevronDown
  Check
} from 'lucide-react';
import Button from './Button';
import { Card } from '../common/card';

interface Language {
  code: string;
  name: string;
  flag: string;
  rtl: boolean;
}

interface LanguageSelectorProps {
  className?: string;
  onLanguageChange?: (language: Language) => void;
}

const languages: Language[] = [
  { code: 'en', name: 'English', flag: '🇺🇸', rtl: false },
  { code: 'es', name: 'Español', flag: '🇪🇸', rtl: false },
  { code: 'fr', name: 'Français', flag: '🇫🇷', rtl: false },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪', rtl: false },
  { code: 'pt', name: 'Português', flag: '🇧🇷', rtl: false },
  { code: 'it', name: 'Italiano', flag: '🇮🇹', rtl: false },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱', rtl: false },
  { code: 'pl', name: 'Polski', flag: '🇵🇱', rtl: false },
  { code: 'ja', name: '日本語', flag: '🇯🇵', rtl: false },
  { code: 'zh', name: '中文', flag: '🇨🇳', rtl: false },
  { code: 'ko', name: '한국어', flag: '🇰🇷', rtl: false },
  { code: 'ar', name: 'العربية', flag: '🇸🇦', rtl: true },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳', rtl: false },
  { code: 'ru', name: 'Русский', flag: '🇷🇺', rtl: false },
  { code: 'tr', name: 'Türkçe', flag: '🇹🇷', rtl: false }
];

const translations: Record<string, Record<string, string>> = {
  // English
  en: {
    select_language: 'Select Language',
    current_language: 'Current Language',
    compliance: 'Compliance',
    training: 'Training',
    feedback: 'Feedback',
    rights: 'Rights',
    dashboard: 'Dashboard',
    analytics: 'Analytics',
    settings: 'Settings',
    logout: 'Logout'
  },
  // Spanish
  es: {
    select_language: 'Seleccionar Idioma',
    current_language: 'Idioma Actual',
    compliance: 'Cumplimiento',
    training: 'Capacitación',
    feedback: 'Comentarios',
    rights: 'Derechos',
    dashboard: 'Panel de Control',
    analytics: 'Análisis',
    settings: 'Configuración',
    logout: 'Cerrar Sesión'
  },
  // French
  fr: {
    select_language: 'Sélectionner la Langue',
    current_language: 'Langue Actuelle',
    compliance: 'Conformité',
    training: 'Formation',
    feedback: 'Commentaires',
    rights: 'Droits',
    dashboard: 'Tableau de Bord',
    analytics: 'Analytique',
    settings: 'Paramètres',
    logout: 'Déconnexion'
  },
  // German
  de: {
    select_language: 'Sprache Auswählen',
    current_language: 'Aktuelle Sprache',
    compliance: 'Einhaltung',
    training: 'Schulung',
    feedback: 'Feedback',
    rights: 'Rechte',
    dashboard: 'Dashboard',
    analytics: 'Analytik',
    settings: 'Einstellungen',
    logout: 'Abmelden'
  },
  // Portuguese
  pt: {
    select_language: 'Selecionar Idioma',
    current_language: 'Idioma Atual',
    compliance: 'Conformidade',
    training: 'Treinamento',
    feedback: 'Feedback',
    rights: 'Direitos',
    dashboard: 'Painel',
    analytics: 'Análise',
    settings: 'Configurações',
    logout: 'Sair'
  },
  // Japanese
  ja: {
    select_language: '言語を選択',
    current_language: '現在の言語',
    compliance: 'コンプライアンス',
    training: '研修',
    feedback: 'フィードバック',
    rights: '権利',
    dashboard: 'ダッシュボード',
    analytics: '分析',
    settings: '設定',
    logout: 'ログアウト'
  },
  // Chinese
  zh: {
    select_language: '选择语言',
    current_language: '当前语言',
    compliance: '合规',
    training: '培训',
    feedback: '反馈',
    rights: '权利',
    dashboard: '仪表板',
    analytics: '分析',
    settings: '设置',
    logout: '退出'
  },
  // Arabic
  ar: {
    select_language: 'اخترار اللغة',
    current_language: 'اللغة الحالية',
    compliance: 'الامتثال',
    training: 'التدريب',
    feedback: 'ملاحظات',
    rights: 'الحقوق',
    dashboard: 'لوحة القيادة',
    analytics: 'التحليلات',
    settings: 'الإعدادات',
    logout: 'تسجيل الخروج'
  }
};

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ className, onLanguageChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState<Language>(languages[0]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Load saved language preference
    const savedLanguage = localStorage.getItem('preferred-language');
    if (savedLanguage) {
      const language = languages.find(lang => lang.code === savedLanguage);
      if (language) {
        setCurrentLanguage(language);
      }
    }
  }, []);

  const handleLanguageSelect = (language: Language) => {
    setCurrentLanguage(language);
    localStorage.setItem('preferred-language', language.code);

    // Update document direction for RTL languages
    document.documentElement.dir = language.rtl ? 'rtl' : 'ltr';
    document.documentElement.lang = language.code;

    if (onLanguageChange) {
      onLanguageChange(language);
    }

    setIsOpen(false);
  };

  const filteredLanguages = languages.filter(lang =>
    lang.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lang.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const translate = (key: string): string => {
    return translations[currentLanguage.code]?.[key] || translations.en[key];
  };

  return (
    <div className={`relative ${className}`}>
      {/* Language Button */}
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        icon={<Globe className="w-4 h-4" />}
      >
        <div className="flex items-center space-x-2">
          <span className="text-lg">{currentLanguage.flag}</span>
          <span className="hidden sm:inline">{currentLanguage.name}</span>
          <ChevronDown className="w-4 h-4" />
        </div>
      </Button>

      {/* Dropdown */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-hidden">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-3">{translate('select_language')}</h3>

              {/* Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder={translate('search_language') || 'Search languages...'}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                />
              </div>
            </div>

            {/* Language List */}
            <div className="overflow-y-auto max-h-64">
              <div className="p-2 space-y-1">
                {filteredLanguages.map((language) => (
                  <button
                    key={language.code}
                    onClick={() => handleLanguageSelect(language)}
                    className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">{language.flag}</span>
                      <div className="text-left">
                        <p className="font-medium text-gray-900">{language.name}</p>
                        <p className="text-sm text-gray-500">{language.code.toUpperCase()}</p>
                      </div>
                    </div>
                    {currentLanguage.code === language.code && (
                      <Check className="w-5 h-5 text-blue-600" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <div className="text-xs text-gray-600">
                <p>Language affects the interface text only.</p>
                <p>Legal documents and policies are available in all supported languages.</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Translation Hook
export const useTranslation = () => {
  const [currentLanguage, setCurrentLanguage] = useState<Language>(languages[0]);

  useEffect(() => {
    const savedLanguage = localStorage.getItem('preferred-language');
    if (savedLanguage) {
      const language = languages.find(lang => lang.code === savedLanguage);
      if (language) {
        setCurrentLanguage(language);
      }
    }
  }, []);

  const translate = (key: string): string => {
    return translations[currentLanguage.code]?.[key] || translations.en[key];
  };

  const setLanguage = (languageCode: string) => {
    const language = languages.find(lang => lang.code === languageCode);
    if (language) {
      setCurrentLanguage(language);
      localStorage.setItem('preferred-language', languageCode);
      document.documentElement.dir = language.rtl ? 'rtl' : 'ltr';
      document.documentElement.lang = languageCode;
    }
  };

  return {
    currentLanguage,
    translate,
    setLanguage,
    isRTL: currentLanguage.rtl
  };
};

// Format date/time according to locale
export const formatDateTime = (date: Date, locale: string = 'en'): string => {
  try {
    return new Intl.DateTimeFormat(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  } catch {
    return date.toLocaleString();
  }
};

// Format number according to locale
export const formatNumber = (
  number: number,
  locale: string = 'en',
  options?: Intl.NumberFormatOptions
): string => {
  try {
    return new Intl.NumberFormat(locale, options).format(number);
  } catch {
    return number.toString();
  }
};

// Currency formatting
export const formatCurrency = (
  amount: number,
  currency: string = 'USD',
  locale: string = 'en'
): string => {
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency
    }).format(amount);
  } catch {
    return `${currency} ${amount.toFixed(2)}`;
  }
};

// Export all supported languages
export { languages };
export { translations };
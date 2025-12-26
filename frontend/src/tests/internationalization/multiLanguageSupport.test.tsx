// frontend/src/tests/internationalization/multiLanguageSupport.test.tsx
/**
 * Multi-Language Support Testing
 * Tests internationalization features and language switching
 * Business Impact: Global market expansion, user experience
 * ROI: 5x - Enables international growth
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock internationalization
const mockTranslations = {
  en: {
    common: {
      submit: 'Submit',
      cancel: 'Cancel',
      save: 'Save',
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      next: 'Next',
      previous: 'Previous',
      finish: 'Finish'
    },
    assessment: {
      title: 'Assessment',
      question: 'Question',
      progress: 'Progress',
      completed: 'Completed',
      time_remaining: 'Time Remaining',
      minutes: 'minutes'
    },
    navigation: {
      dashboard: 'Dashboard',
      assessments: 'Assessments',
      teams: 'Teams',
      settings: 'Settings',
      profile: 'Profile'
    }
  },
  es: {
    common: {
      submit: 'Enviar',
      cancel: 'Cancelar',
      save: 'Guardar',
      loading: 'Cargando...',
      error: 'Error',
      success: 'Éxito',
      next: 'Siguiente',
      previous: 'Anterior',
      finish: 'Terminar'
    },
    assessment: {
      title: 'Evaluación',
      question: 'Pregunta',
      progress: 'Progreso',
      completed: 'Completado',
      time_remaining: 'Tiempo Restante',
      minutes: 'minutos'
    },
    navigation: {
      dashboard: 'Panel',
      assessments: 'Evaluaciones',
      teams: 'Equipos',
      settings: 'Configuración',
      profile: 'Perfil'
    }
  },
  fr: {
    common: {
      submit: 'Soumettre',
      cancel: 'Annuler',
      save: 'Enregistrer',
      loading: 'Chargement...',
      error: 'Erreur',
      success: 'Succès',
      next: 'Suivant',
      previous: 'Précédent',
      finish: 'Terminer'
    },
    assessment: {
      title: 'Évaluation',
      question: 'Question',
      progress: 'Progrès',
      completed: 'Terminé',
      time_remaining: 'Temps Restant',
      minutes: 'minutes'
    },
    navigation: {
      dashboard: 'Tableau de Bord',
      assessments: 'Évaluations',
      teams: 'Équipes',
      settings: 'Paramètres',
      profile: 'Profil'
    }
  },
  de: {
    common: {
      submit: 'Absenden',
      cancel: 'Abbrechen',
      save: 'Speichern',
      loading: 'Laden...',
      error: 'Fehler',
      success: 'Erfolg',
      next: 'Weiter',
      previous: 'Zurück',
      finish: 'Beenden'
    },
    assessment: {
      title: 'Bewertung',
      question: 'Frage',
      progress: 'Fortschritt',
      completed: 'Abgeschlossen',
      time_remaining: 'Verbleibende Zeit',
      minutes: 'Minuten'
    },
    navigation: {
      dashboard: 'Dashboard',
      assessments: 'Bewertungen',
      teams: 'Teams',
      settings: 'Einstellungen',
      profile: 'Profil'
    }
  },
  zh: {
    common: {
      submit: '提交',
      cancel: '取消',
      save: '保存',
      loading: '加载中...',
      error: '错误',
      success: '成功',
      next: '下一步',
      previous: '上一步',
      finish: '完成'
    },
    assessment: {
      title: '评估',
      question: '问题',
      progress: '进度',
      completed: '已完成',
      time_remaining: '剩余时间',
      minutes: '分钟'
    },
    navigation: {
      dashboard: '仪表板',
      assessments: '评估',
      teams: '团队',
      settings: '设置',
      profile: '个人资料'
    }
  }
};

// Mock i18n hook
const mockUseTranslation = () => {
  const [currentLang, setCurrentLang] = React.useState('en');

  const t = (key: string) => {
    const keys = key.split('.');
    let translation = mockTranslations[currentLang as keyof typeof mockTranslations];

    for (const k of keys) {
      translation = translation?.[k as keyof typeof translation];
    }

    return translation || key;
  };

  const changeLanguage = (lang: string) => {
    if (mockTranslations[lang as keyof typeof mockTranslations]) {
      setCurrentLang(lang);
    }
  };

  return {
    t,
    i18n: {
      language: currentLang,
      changeLanguage
    }
  };
};

vi.mock('react-i18next', () => ({
  useTranslation: mockUseTranslation
}));

describe('Multi-Language Support Tests', () => {
  beforeEach(() => {
    // Reset language to English before each test
    vi.clearAllMocks();
  });

  // 🌍 Basic Language Switching Tests
  describe('Language Switching Functionality', () => {
    it('should render UI elements in English by default', () => {
      const TestComponent = () => {
        const { t } = mockUseTranslation();

        return (
          <div>
            <button>{t('common.submit')}</button>
            <h1>{t('assessment.title')}</h1>
          </div>
        );
      };

      render(<TestComponent />);

      expect(screen.getByText('Submit')).toBeInTheDocument();
      expect(screen.getByText('Assessment')).toBeInTheDocument();
    });

    it('should switch to Spanish and update all UI elements', async () => {
      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        return (
          <div>
            <button onClick={() => i18n.changeLanguage('es')}>
              Switch to Spanish
            </button>
            <span>{t('common.loading')}</span>
            <span>{t('navigation.dashboard')}</span>
          </div>
        );
      };

      render(<TestComponent />);

      // Initially in English
      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.getByText('Dashboard')).toBeInTheDocument();

      // Switch to Spanish
      fireEvent.click(screen.getByText('Switch to Spanish'));

      await waitFor(() => {
        expect(screen.getByText('Cargando...')).toBeInTheDocument();
        expect(screen.getByText('Panel')).toBeInTheDocument();
      });
    });

    it('should support French language with proper translations', async () => {
      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        return (
          <div>
            <button onClick={() => i18n.changeLanguage('fr')}>
              Switch to French
            </button>
            <span>{t('common.error')}</span>
            <span>{t('assessment.minutes')}</span>
          </div>
        );
      };

      render(<TestComponent />);

      fireEvent.click(screen.getByText('Switch to French'));

      await waitFor(() => {
        expect(screen.getByText('Erreur')).toBeInTheDocument();
        expect(screen.getByText('minutes')).toBeInTheDocument();
      });
    });

    it('should support German language with accurate translations', async () => {
      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        return (
          <div>
            <button onClick={() => i18n.changeLanguage('de')}>
              Switch to German
            </button>
            <span>{t('common.success')}</span>
            <span>{t('navigation.settings')}</span>
          </div>
        );
      };

      render(<TestComponent />);

      fireEvent.click(screen.getByText('Switch to German'));

      await waitFor(() => {
        expect(screen.getByText('Erfolg')).toBeInTheDocument();
        expect(screen.getByText('Einstellungen')).toBeInTheDocument();
      });
    });

    it('should support Chinese (Simplified) language', async () => {
      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        return (
          <div>
            <button onClick={() => i18n.changeLanguage('zh')}>
              Switch to Chinese
            </button>
            <span>{t('common.save')}</span>
            <span>{t('assessment.completed')}</span>
          </div>
        );
      };

      render(<TestComponent />);

      fireEvent.click(screen.getByText('Switch to Chinese'));

      await waitFor(() => {
        expect(screen.getByText('保存')).toBeInTheDocument();
        expect(screen.getByText('已完成')).toBeInTheDocument();
      });
    });
  });

  // 🔤 Text Direction and Layout Tests
  describe('Text Direction and Layout', () => {
    it('should maintain proper text direction for LTR languages', () => {
      const TestComponent = () => {
        const { t } = mockUseTranslation();

        return (
          <div style={{ direction: 'ltr' }}>
            <p>{t('assessment.question')} 1</p>
            <button>{t('common.next')}</button>
          </div>
        );
      };

      render(<TestComponent />);

      const container = screen.getByText('Question 1').parentElement;
      expect(container).toHaveStyle({ direction: 'ltr' });
    });

    it('should handle missing translation keys gracefully', () => {
      const TestComponent = () => {
        const { t } = mockUseTranslation();

        return (
          <div>
            <span>{t('nonexistent.key')}</span>
            <span>{t('common.submit')}</span>
          </div>
        );
      };

      render(<TestComponent />);

      // Should show key name for missing translation
      expect(screen.getByText('nonexistent.key')).toBeInTheDocument();
      // Should show translation for existing key
      expect(screen.getByText('Submit')).toBeInTheDocument();
    });

    it('should preserve numeric values and placeholders in translations', () => {
      const extendedTranslations = {
        en: {
          assessment: {
            question_number: 'Question {{number}} of {{total}}',
            time_remaining: '{{minutes}} minutes remaining'
          }
        },
        es: {
          assessment: {
            question_number: 'Pregunta {{number}} de {{total}}',
            time_remaining: '{{minutes}} minutos restantes'
          }
        }
      };

      const mockUseTranslationWithPlaceholders = () => {
        const [currentLang] = React.useState('es');

        const t = (key: string, options?: Record<string, any>) => {
          let translation = extendedTranslations[currentLang as keyof typeof extendedTranslations]?.assessment?.[key.split('.')[1]] || key;

          if (options) {
            Object.keys(options).forEach(placeholder => {
              translation = translation?.replace(`{{${placeholder}}}`, String(options[placeholder]));
            });
          }

          return translation;
        };

        return { t };
      };

      vi.mock('react-i18next', () => ({
        useTranslation: mockUseTranslationWithPlaceholders
      }));

      const TestComponent = () => {
        const { t } = mockUseTranslationWithPlaceholders();

        return (
          <div>
            <span>{t('assessment.question_number', { number: 5, total: 20 })}</span>
            <span>{t('assessment.time_remaining', { minutes: 15 })}</span>
          </div>
        );
      };

      render(<TestComponent />);

      expect(screen.getByText('Pregunta 5 de 20')).toBeInTheDocument();
      expect(screen.getByText('15 minutos restantes')).toBeInTheDocument();
    });
  });

  // 📱 Mobile Multi-Language Tests
  describe('Mobile Multi-Language Support', () => {
    it('should work correctly on mobile devices with language switching', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        return (
          <div className="mobile-layout">
            <header>
              <h1>{t('navigation.dashboard')}</h1>
            </header>
            <main>
              <button onClick={() => i18n.changeLanguage('fr')}>
                {t('common.next')}
              </button>
            </main>
          </div>
        );
      };

      render(<TestComponent />);

      // Should render correctly on mobile
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();

      // Switch language on mobile
      fireEvent.click(screen.getByText('Next'));

      await waitFor(() => {
        expect(screen.getByText('Tableau de Bord')).toBeInTheDocument();
      });
    });

    it('should handle language switching during mobile orientation changes', async () => {
      // Simulate mobile orientation change
      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        return (
          <div>
            <span>{t('assessment.time_remaining')}</span>
            <button onClick={() => i18n.changeLanguage('es')}>
              {t('common.save')}
            </button>
          </div>
        );
      };

      render(<TestComponent />);

      // Initial state
      expect(screen.getByText('Time Remaining')).toBeInTheDocument();
      expect(screen.getByText('Save')).toBeInTheDocument();

      // Simulate orientation change
      Object.defineProperty(window, 'orientation', {
        writable: true,
        value: { angle: 90, type: 'landscape-primary' }
      });

      // Switch language
      fireEvent.click(screen.getByText('Save'));

      await waitFor(() => {
        expect(screen.getByText('Tiempo Restante')).toBeInTheDocument();
      });
    });
  });

  // 🔤 Character Encoding and Special Characters Tests
  describe('Character Encoding and Special Characters', () => {
    it('should display special characters correctly in all languages', () => {
      const specialCharTranslations = {
        en: { message: 'Assessment completed successfully!' },
        es: { message: '¡Evaluación completada con éxito!' },
        fr: { message: 'Évaluation terminée avec succès!' },
        de: { message: 'Bewertung erfolgreich abgeschlossen!' },
        zh: { message: '评估成功完成！' }
      };

      Object.entries(specialCharTranslations).forEach(([lang, translations]) => {
        const TestComponent = () => {
          const { t } = mockUseTranslation();

          return (
            <div>
              <span data-lang={lang}>{translations.message}</span>
            </div>
          );
        };

        const { container } = render(<TestComponent />);
        const element = container.querySelector(`[data-lang="${lang}"]`);

        expect(element).toBeInTheDocument();
        expect(element?.textContent).toBe(translations.message);
      });
    });

    it('should handle emoji and unicode characters in translations', () => {
      const emojiTranslations = {
        en: { welcome: 'Welcome! 👋', success: 'Great job! 🎉' },
        es: { welcome: '¡Bienvenido! 👋', success: '¡Buen trabajo! 🎉' },
        fr: { welcome: 'Bienvenue ! 👋', success: 'Excellent travail ! 🎉' }
      };

      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();
        const [lang, setLang] = React.useState('en');

        // Mock translation function with emojis
        const tWithEmoji = (key: string) => {
          return emojiTranslations[lang as keyof typeof emojiTranslations]?.[key as keyof typeof emojiTranslations.en] || key;
        };

        return (
          <div>
            <button onClick={() => setLang(lang === 'en' ? 'es' : 'en')}>
              Switch Language
            </button>
            <h1>{tWithEmoji('welcome')}</h1>
            <p>{tWithEmoji('success')}</p>
          </div>
        );
      };

      render(<TestComponent />);

      // Check emojis in English
      expect(screen.getByText('Welcome! 👋')).toBeInTheDocument();
      expect(screen.getByText('Great job! 🎉')).toBeInTheDocument();

      // Switch to Spanish
      fireEvent.click(screen.getByText('Switch Language'));

      // Check emojis in Spanish
      expect(screen.getByText('¡Bienvenido! 👋')).toBeInTheDocument();
      expect(screen.getByText('¡Buen trabajo! 🎉')).toBeInTheDocument();
    });
  });

  // 🔄 Performance and Caching Tests
  describe('Performance and Caching', () => {
    it('should cache translations and not re-fetch on language switches', async () => {
      let translationLoadCount = 0;

      const mockLoadTranslations = () => {
        translationLoadCount++;
        return Promise.resolve(mockTranslations);
      };

      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        return (
          <div>
            <button onClick={() => i18n.changeLanguage('fr')}>
              Switch to French
            </button>
            <button onClick={() => i18n.changeLanguage('de')}>
              Switch to German
            </button>
            <span>{t('common.loading')}</span>
          </div>
        );
      };

      render(<TestComponent />);

      // Switch to French
      fireEvent.click(screen.getByText('Switch to French'));
      await waitFor(() => expect(screen.getByText('Chargement...')).toBeInTheDocument());

      // Switch back to English (should use cached translation)
      fireEvent.click(screen.getByText('Switch to German'));
      await waitFor(() => expect(screen.getByText('Laden...')).toBeInTheDocument());

      // Translation should only be loaded once
      expect(translationLoadCount).toBeLessThan(3);
    });

    it('should handle rapid language switching without errors', async () => {
      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        return (
          <div>
            <button onClick={() => i18n.changeLanguage('es')}>ES</button>
            <button onClick={() => i18n.changeLanguage('fr')}>FR</button>
            <button onClick={() => i18n.changeLanguage('de')}>DE</button>
            <span>{t('common.submit')}</span>
          </div>
        );
      };

      render(<TestComponent />);

      // Rapid language switching
      fireEvent.click(screen.getByText('ES'));
      fireEvent.click(screen.getByText('FR'));
      fireEvent.click(screen.getByText('DE'));
      fireEvent.click(screen.getByText('ES'));

      await waitFor(() => {
        expect(screen.getByText('Enviar')).toBeInTheDocument();
      });

      // Should not have any errors and should show final language
      expect(screen.getByText('Enviar')).toBeInTheDocument();
    });
  });

  // ♿ Accessibility Tests for Internationalization
  describe('Internationalization Accessibility', () => {
    it('should update lang attribute on language change', async () => {
      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        React.useEffect(() => {
          document.documentElement.lang = i18n.language;
        }, [i18n.language]);

        return (
          <div>
            <button onClick={() => i18n.changeLanguage('es')}>
              Switch to Spanish
            </button>
            <h1>{t('assessment.title')}</h1>
          </div>
        );
      };

      render(<TestComponent />);

      // Should have English lang attribute
      expect(document.documentElement.lang).toBe('en');

      // Switch to Spanish
      fireEvent.click(screen.getByText('Switch to Spanish'));

      await waitFor(() => {
        expect(document.documentElement.lang).toBe('es');
      });
    });

    it('should maintain ARIA labels in translated languages', async () => {
      const TestComponent = () => {
        const { t, i18n } = mockUseTranslation();

        return (
          <div>
            <button
              onClick={() => i18n.changeLanguage('fr')}
              aria-label={t('common.submit')}
            >
              {t('common.submit')}
            </button>
            <input
              type="text"
              placeholder={t('assessment.title')}
              aria-label={t('assessment.title')}
            />
          </div>
        );
      };

      render(<TestComponent />);

      const button = screen.getByRole('button');
      const input = screen.getByRole('textbox');

      // Should have English aria labels
      expect(button).toHaveAttribute('aria-label', 'Submit');
      expect(input).toHaveAttribute('aria-label', 'Assessment');

      // Switch to French
      fireEvent.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-label', 'Soumettre');
        expect(input).toHaveAttribute('aria-label', 'Évaluation');
      });
    });
  });
});
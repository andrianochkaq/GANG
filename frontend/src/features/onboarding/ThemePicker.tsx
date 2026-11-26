import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';

import { profileApi } from '../../api/profile';
import type { ProfilePatch } from '../../api/profileTypes';
import BaseColorPicker from '../../components/ui/BaseColorPicker';
import { useThemeStore } from '../../store/themeStore';
import { THEMES, isThemeId } from '../../theme/themes';
import AuthErrorMessage from '../auth/AuthErrorMessage';
import TheAuthLayout from '../auth/TheAuthLayout';
import { getRedirectTarget } from '../auth/useFinishLogin';
import ThemePickerPreview from './ThemePickerPreview';
import { PROFILE_QUERY_KEY } from './useProfile';

// Step 3 of 3 of the registration: boards Color3 and DColor.
const STEP_PROGRESS_PERCENT = 100;

// Shown once after the first login. Choosing a swatch recolours the whole
// app at once; the primary button saves it, the text button skips and keeps
// the saved colour (white). Both mark onboarding as done through /api/me/.
export default function ThemePicker() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const themeId = useThemeStore((state) => state.themeId);
  const setThemeId = useThemeStore((state) => state.setThemeId);

  const save = useMutation({
    mutationFn: (patch: ProfilePatch) => profileApi.updateProfile(patch),
    onSuccess: (profile) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, profile);
      // After a skip this puts the preview back to the saved colour.
      setThemeId(profile.themeColor);
      navigate(getRedirectTarget(location.state), { replace: true });
    },
  });

  const options = THEMES.map((theme) => ({
    id: theme.id,
    label: t(`theme.colors.${theme.id}`),
    swatch: theme.swatch,
  }));

  function handleChange(id: string) {
    if (isThemeId(id)) {
      setThemeId(id);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!save.isPending) {
      save.mutate({ themeColor: themeId, isOnboardingDone: true });
    }
  }

  function handleSkip() {
    if (!save.isPending) {
      save.mutate({ isOnboardingDone: true });
    }
  }

  return (
    <TheAuthLayout
      brandTitle={t('onboarding.color.brandTitle')}
      brandText={t('onboarding.color.brandText')}
      brandSteps={{
        title: t('auth.verify.howTitle'),
        items: [t('auth.verify.howStep1'), t('auth.verify.howStep2'), t('auth.verify.howStep3')],
      }}
    >
      <div className="fc-steps">
        <span className="fc-steps__label">{t('onboarding.color.step')}</span>
        <div
          className="fc-progress"
          role="progressbar"
          aria-label={t('onboarding.color.step')}
          aria-valuenow={STEP_PROGRESS_PERCENT}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <span style={{ width: `${STEP_PROGRESS_PERCENT}%` }} />
        </div>
      </div>

      <div className="fc-auth__intro">
        <h1 className="fc-auth__title">{t('onboarding.color.title')}</h1>
        <p className="fc-auth__text">{t('onboarding.color.text')}</p>
      </div>

      <form className="fc-auth__fields" onSubmit={handleSubmit} noValidate>
        <ThemePickerPreview themeName={t(`theme.colors.${themeId}`)} />
        <div className="fc-card">
          <BaseColorPicker
            options={options}
            value={themeId}
            onChange={handleChange}
            label={t('onboarding.color.paletteLabel')}
            isDisabled={save.isPending}
          />
        </div>
        <AuthErrorMessage error={save.error} />
        <button
          type="submit"
          className="fc-btn fc-btn--primary fc-btn--block"
          aria-busy={save.isPending || undefined}
        >
          {t('onboarding.color.submit')}
        </button>
        <button type="button" className="fc-btn fc-btn--text fc-btn--block" onClick={handleSkip}>
          {t('onboarding.color.skip')}
        </button>
        <p className="fc-auth__note">{t('onboarding.color.note')}</p>
      </form>
    </TheAuthLayout>
  );
}

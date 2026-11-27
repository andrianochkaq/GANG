import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';

import { getAuthErrorMessageKey } from '../../api/authErrors';
import type { Fridge } from '../../api/fridgesTypes';
import NavIcon from '../../components/layout/NavIcon';
import { APP_PATHS } from '../../routes/paths';
import FridgeNameForm from './FridgeNameForm';
import {
  findCurrentFridge,
  useCreateFridge,
  useFridges,
  useRenameFridge,
  useSelectFridge,
} from './useFridges';

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), [tabindex="0"]';

// The fridge list (boards Fridges, DFridges): a bottom sheet on phones,
// a centred dialog from 1024 px. Picking a fridge switches all fridge data
// and closes the list; the owner can rename a fridge or add a new one.
export default function FridgeSwitcher() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const dialogRef = useRef<HTMLDivElement>(null);
  const fridgesQuery = useFridges();
  const selectFridge = useSelectFridge();
  const renameFridge = useRenameFridge();
  const createFridge = useCreateFridge();
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const fridges = fridgesQuery.data;
  const currentId = findCurrentFridge(fridges)?.id;

  // Focus moves into the dialog and goes back to the opener (the sidebar card
  // stays on screen on desktop) when it closes.
  useEffect(() => {
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialogRef.current?.focus();
    return () => {
      if (opener?.isConnected) {
        opener.focus();
      }
    };
  }, []);

  function close() {
    // Opened from inside the app: go back to that screen; opened by URL: home.
    if (location.key !== 'default') {
      navigate(-1);
    } else {
      navigate(APP_PATHS.home, { replace: true });
    }
  }

  // Listened on the document, so Esc and Tab still work when the focused
  // element has just gone (a rename form closes after saving).
  const handleKeyDownRef = useRef<(event: KeyboardEvent) => void>(() => undefined);
  handleKeyDownRef.current = (event: KeyboardEvent) => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    if (event.key === 'Escape') {
      event.preventDefault();
      close();
      return;
    }
    if (event.key !== 'Tab') {
      return;
    }
    // Keep Tab inside the dialog while it is open.
    const items = Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE));
    const first = items[0];
    const last = items[items.length - 1];
    if (!first || !last) {
      return;
    }
    const active = document.activeElement;
    const isInside = active instanceof Node && dialog.contains(active) && active !== dialog;
    if (!isInside) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus();
    } else if (event.shiftKey && active === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => handleKeyDownRef.current(event);
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, []);

  // A closed form takes the focused field with it; keep focus in the dialog.
  function closeForm() {
    setRenamingId(null);
    setIsCreating(false);
    dialogRef.current?.focus();
  }

  function pick(fridge: Fridge) {
    if (fridge.id === currentId) {
      close();
      return;
    }
    selectFridge.mutate(fridge.id, { onSuccess: close });
  }

  function startRename(fridgeId: string) {
    renameFridge.reset();
    setIsCreating(false);
    setRenamingId(fridgeId);
  }

  function startCreate() {
    createFridge.reset();
    setRenamingId(null);
    setIsCreating(true);
  }

  const selectError = selectFridge.isError ? getAuthErrorMessageKey(selectFridge.error) : null;

  return (
    <div className="fc-switcher">
      <div className="fc-switcher__scrim" aria-hidden="true" onClick={close} />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="fridges-title"
        aria-describedby="fridges-text"
        className="fc-switcher__dialog"
        tabIndex={-1}
      >
        <span className="fc-switcher__handle" aria-hidden="true" />
        <div className="fc-switcher__head">
          <div className="fc-switcher__heading">
            <h1 id="fridges-title" className="fc-switcher__title">
              {t('fridges.title')}
            </h1>
            <p id="fridges-text" className="fc-switcher__text">
              {t('fridges.text')}
            </p>
          </div>
          <button
            type="button"
            className="fc-iconbtn fc-switcher__close"
            aria-label={t('fridges.close')}
            onClick={close}
          >
            <NavIcon name="close" />
          </button>
        </div>

        {fridgesQuery.isPending && <p className="fc-switcher__status">{t('fridges.loading')}</p>}

        {fridgesQuery.isError && (
          <div className="fc-switcher__status" role="alert">
            <p>{t('fridges.loadError')}</p>
            <button
              type="button"
              className="fc-btn fc-btn--sm fc-btn--secondary"
              onClick={() => void fridgesQuery.refetch()}
            >
              {t('fridges.retry')}
            </button>
          </div>
        )}

        {selectError && (
          <p className="fc-field__error" role="alert">
            {t('fridges.selectError')}
          </p>
        )}

        {fridges && (
          <ul className="fc-switcher__list" aria-busy={selectFridge.isPending || undefined}>
            {fridges.map((fridge) => (
              <li key={fridge.id}>
                {renamingId === fridge.id ? (
                  <FridgeNameForm
                    label={t('fridges.newName')}
                    submitLabel={t('fridges.save')}
                    initialName={fridge.name}
                    meta={<FridgeMeta fridge={fridge} />}
                    isSaving={renameFridge.isPending}
                    error={renameFridge.error}
                    onCancel={closeForm}
                    onSubmit={(name) =>
                      renameFridge.mutate({ fridgeId: fridge.id, name }, { onSuccess: closeForm })
                    }
                  />
                ) : (
                  <FridgeRow
                    fridge={fridge}
                    isCurrent={fridge.id === currentId}
                    isSwitching={selectFridge.isPending && selectFridge.variables === fridge.id}
                    onPick={() => pick(fridge)}
                    onRename={() => startRename(fridge.id)}
                  />
                )}
              </li>
            ))}
          </ul>
        )}

        {fridges &&
          (isCreating ? (
            <FridgeNameForm
              label={t('fridges.createLabel')}
              submitLabel={t('fridges.create')}
              isSaving={createFridge.isPending}
              error={createFridge.error}
              onCancel={closeForm}
              onSubmit={(name) => createFridge.mutate(name, { onSuccess: closeForm })}
            />
          ) : (
            <button type="button" className="fc-switcher__new" onClick={startCreate}>
              <NavIcon name="plus" />
              {t('fridges.newFridge')}
            </button>
          ))}
      </div>
    </div>
  );
}

function FridgeMeta({ fridge }: { fridge: Fridge }) {
  const { t } = useTranslation();
  const members =
    fridge.memberCount <= 1
      ? t('fridges.onlyYou')
      : t('fridges.members', { count: fridge.memberCount });
  return (
    <>
      {t('fridges.meta', {
        members,
        products: t('fridges.products', { count: fridge.productCount }),
      })}
    </>
  );
}

type FridgeRowProps = {
  fridge: Fridge;
  isCurrent: boolean;
  isSwitching: boolean;
  onPick: () => void;
  onRename: () => void;
};

function FridgeRow({ fridge, isCurrent, isSwitching, onPick, onRename }: FridgeRowProps) {
  const { t } = useTranslation();

  return (
    <div className={isCurrent ? 'fc-switcher__row fc-switcher__row--current' : 'fc-switcher__row'}>
      <button
        type="button"
        className="fc-switcher__pick"
        aria-current={isCurrent ? 'true' : undefined}
        disabled={isSwitching}
        onClick={onPick}
      >
        <span className="fc-switcher__icon">
          <NavIcon name={isCurrent ? 'home' : 'house'} />
        </span>
        <span className="fc-switcher__main">
          <span className="fc-switcher__name">{fridge.name}</span>
          <span className="fc-switcher__meta">
            <FridgeMeta fridge={fridge} />
          </span>
        </span>
        {isCurrent && <span className="fc-badge fc-badge--soft">{t('fridges.current')}</span>}
      </button>
      {fridge.role === 'owner' && (
        <button
          type="button"
          className="fc-iconbtn fc-iconbtn--ghost"
          aria-label={t('fridges.rename', { name: fridge.name })}
          onClick={onRename}
        >
          <NavIcon name="pencil" />
        </button>
      )}
    </div>
  );
}

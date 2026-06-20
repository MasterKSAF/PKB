import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  MenuItem,
  Paper,
  Stack,
  Switch,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  FileText,
  FlaskConical,
  Plus,
  RefreshCw,
  Save,
  Trash2,
  Upload,
  X,
} from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useUIStore } from '../store/uiStore';
import { registryApi, type RegistryClassifierNode, type RegistryClassifierPending, type RegistryTerminologyEntry } from '../utils/http';

type RegistryTab = 'classifiers' | 'terminology';
type ClassifierView = 'list' | 'tree' | 'pending' | 'validate';

type ClassifierFormState = {
  classifierSystem: string;
  code: string;
  parentCode: string;
  fullName: string;
  status: string;
  effectiveDate: string;
  replacedBy: string;
};

type TerminologyFormState = {
  rawTerm: string;
  standardTerm: string;
  normalizedValue: string;
  termType: string;
  isCaseSensitive: boolean;
  definition: string;
  synonyms: string[];
  relatedDocs: string[];
  scope: string[];
  isBlocked: boolean;
};

type PendingAction = {
  mode: 'accept' | 'reject';
  item: RegistryClassifierPending;
};

const CLASSIFIER_SYSTEM_OPTIONS = ['MKS', 'OKSTU', 'UDC', 'EXTERNAL'];
const CLASSIFIER_STATUS_OPTIONS = ['active', 'deprecated', 'archived'];
const PENDING_STATUS_OPTIONS = ['new', 'mapped', 'rejected'];
const TERMINOLOGY_TYPE_OPTIONS = ['acronym', 'foreign_term', 'standard_code', 'avatar', 'symbol'];

const panelSx = (isLight: boolean) => ({
  borderRadius: 3,
  bgcolor: isLight ? 'rgba(255, 255, 255, 0.88)' : 'rgba(22, 23, 27, 0.72)',
  borderColor: isLight ? 'rgba(14, 116, 144, 0.22)' : 'rgba(198, 216, 240, 0.34)',
  borderWidth: 1.5,
  boxShadow: isLight ? '0 8px 22px rgba(15,23,42,0.05)' : 'inset 0 1px 0 rgba(255,255,255,0.045)',
} as const);

const sectionHeaderSx = (isLight: boolean) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: 1,
  pb: 0.85,
  borderBottom: `2px solid ${isLight ? 'rgba(14, 116, 144, 0.24)' : 'rgba(198, 214, 236, 0.26)'}`,
} as const);

const tableSx = {
  '& .MuiTableCell-root': {
    borderBottomColor: 'rgba(198, 216, 240, 0.22)',
    py: 1.1,
    px: 1.25,
  },
  '& .MuiTableHead-root .MuiTableCell-root': {
    fontWeight: 600,
    color: 'inherit',
    whiteSpace: 'nowrap',
  },
  '& .MuiTableBody-root .MuiTableRow-root:nth-of-type(odd)': {
    bgcolor: 'rgba(255,255,255,0.016)',
  },
  '& .MuiTableBody-root .MuiTableRow-root:hover': {
    bgcolor: 'rgba(123, 166, 227, 0.05)',
  },
} as const;

function extractApiMessage(error: any) {
  return (
    error?.response?.data?.detail ??
    error?.response?.data?.message ??
    error?.response?.data?.error?.message ??
    error?.message ??
    'Не удалось выполнить действие.'
  );
}

function initialClassifierDraft(system = 'MKS'): ClassifierFormState {
  return {
    classifierSystem: system,
    code: '',
    parentCode: '',
    fullName: '',
    status: 'active',
    effectiveDate: '',
    replacedBy: '',
  };
}

function initialTermDraft(): TerminologyFormState {
  return {
    rawTerm: '',
    standardTerm: '',
    normalizedValue: '',
    termType: 'acronym',
    isCaseSensitive: false,
    definition: '',
    synonyms: [],
    relatedDocs: [],
    scope: [],
    isBlocked: false,
  };
}

function classifierDraftFromNode(node: RegistryClassifierNode | null | undefined, fallbackSystem = 'MKS'): ClassifierFormState {
  if (!node) return initialClassifierDraft(fallbackSystem);

  return {
    classifierSystem: node.classifier_system || fallbackSystem,
    code: node.code ?? '',
    parentCode: node.parent_code ?? '',
    fullName: node.full_name ?? '',
    status: node.status ?? 'active',
    effectiveDate: node.effective_date ?? '',
    replacedBy: node.replaced_by ?? '',
  };
}

function termDraftFromNode(node: RegistryTerminologyEntry | null | undefined): TerminologyFormState {
  if (!node) return initialTermDraft();

  return {
    rawTerm: node.raw_term ?? '',
    standardTerm: node.standard_term ?? '',
    normalizedValue: node.normalized_value ?? '',
    termType: node.term_type ?? 'acronym',
    isCaseSensitive: Boolean(node.is_case_sensitive),
    definition: node.definition ?? '',
    synonyms: Array.isArray(node.synonyms) ? node.synonyms : [],
    relatedDocs: Array.isArray(node.related_docs) ? node.related_docs : [],
    scope: Array.isArray(node.scope) ? node.scope : [],
    isBlocked: Boolean(node.is_blocked),
  };
}

function classifierPayloadFromDraft(draft: ClassifierFormState) {
  return {
    classifier_system: draft.classifierSystem,
    code: draft.code.trim(),
    parent_code: draft.parentCode.trim() || undefined,
    full_name: draft.fullName.trim(),
    status: draft.status,
    effective_date: draft.effectiveDate.trim() || undefined,
    replaced_by: draft.replacedBy.trim() || undefined,
  };
}

function termPayloadFromDraft(draft: TerminologyFormState) {
  return {
    raw_term: draft.rawTerm.trim(),
    standard_term: draft.standardTerm.trim(),
    normalized_value: draft.normalizedValue.trim(),
    term_type: draft.termType,
    is_case_sensitive: draft.isCaseSensitive,
    definition: draft.definition.trim() || undefined,
    synonyms: draft.synonyms,
    related_docs: draft.relatedDocs,
    scope: draft.scope,
    is_blocked: draft.isBlocked,
  };
}

function splitTags(value: string) {
  return value
    .split(/[,\n;]/g)
    .map((item) => item.trim())
    .filter(Boolean);
}

const TagField: React.FC<{
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
}> = ({ label, values, onChange, placeholder, disabled }) => {
  const [draft, setDraft] = useState('');

  const commit = () => {
    const next = splitTags(draft);
    if (!next.length) return;
    onChange(Array.from(new Set([...values, ...next])));
    setDraft('');
  };

  return (
    <Stack spacing={1}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 0.75,
          p: 1,
          borderRadius: 2,
          border: '1px solid',
          borderColor: 'rgba(198, 216, 240, 0.22)',
          bgcolor: 'rgba(255,255,255,0.02)',
          minHeight: 44,
        }}
      >
        {values.map((value) => (
          <Chip
            key={value}
            label={value}
            size="small"
            onDelete={
              disabled
                ? undefined
                : () => {
                    onChange(values.filter((item) => item !== value));
                  }
            }
          />
        ))}
        <TextField
          variant="standard"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ',' || event.key === ';') {
              event.preventDefault();
              commit();
            }
          }}
          onBlur={commit}
          placeholder={placeholder}
          disabled={disabled}
          sx={{ minWidth: 180, flex: '1 1 180px' }}
        />
      </Box>
    </Stack>
  );
};

const TreeNode: React.FC<{
  node: RegistryClassifierNode;
  depth: number;
  selectedCode?: string;
  onSelect: (node: RegistryClassifierNode) => void;
}> = ({ node, depth, selectedCode, onSelect }) => {
  const children = Array.isArray(node.children) ? node.children : [];
  const isSelected = selectedCode === node.code;
  const hasChildren = children.length > 0;

  return (
    <Box sx={{ pl: depth * 2 }}>
      <Button
        fullWidth
        variant={isSelected ? 'contained' : 'text'}
        onClick={() => onSelect(node)}
        sx={{
          justifyContent: 'flex-start',
          textTransform: 'none',
          mb: 0.65,
          px: 1.2,
          py: 0.8,
          color: isSelected ? undefined : 'inherit',
        }}
      >
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', width: '100%' }}>
          {hasChildren ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography sx={{ fontSize: '0.89rem', fontWeight: 520 }}>{node.full_name}</Typography>
            <Typography variant="caption" color="text.secondary">
              {node.classifier_system} · {node.code}
            </Typography>
          </Box>
          {typeof node.documents_count === 'number' && (
            <Chip size="small" label={`${node.documents_count}`} variant="outlined" sx={{ ml: 'auto' }} />
          )}
        </Stack>
      </Button>
      {hasChildren && (
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          {children.map((child) => (
            <TreeNode key={`${child.classifier_system}-${child.code}`} node={child} depth={depth + 1} selectedCode={selectedCode} onSelect={onSelect} />
          ))}
        </Box>
      )}
    </Box>
  );
};

export const RegistryEditors: React.FC = () => {
  const { currentPermissions, currentRole, themeMode, workMode } = useUIStore();
  const queryClient = useQueryClient();
  const isLight = themeMode === 'light';
  const isDemo = workMode === 'demo';

  const [registryTab, setRegistryTab] = useState<RegistryTab>('classifiers');
  const [classifierView, setClassifierView] = useState<ClassifierView>('list');
  const [classifierSystem, setClassifierSystem] = useState('MKS');
  const [classifierFilters, setClassifierFilters] = useState({
    code: '',
    fullName: '',
    status: '',
    parentCode: '',
    page: 1,
    pageSize: 25,
  });
  const [treeFilters, setTreeFilters] = useState({
    rootCode: '',
    maxDepth: 10,
    search: '',
    status: '',
  });
  const [pendingFilters, setPendingFilters] = useState({
    system: 'MKS',
    status: '',
    page: 1,
    pageSize: 25,
  });
  const [selectedClassifierKey, setSelectedClassifierKey] = useState<{ system: string; code: string } | null>(null);
  const [classifierDraft, setClassifierDraft] = useState(initialClassifierDraft(classifierSystem));
  const [classifierNotice, setClassifierNotice] = useState('');
  const [classifierError, setClassifierError] = useState('');
  const [classifierDeleteOpen, setClassifierDeleteOpen] = useState(false);
  const [classifierImportOpen, setClassifierImportOpen] = useState(false);
  const [classifierImportFile, setClassifierImportFile] = useState<File | null>(null);
  const [classifierImportMapping, setClassifierImportMapping] = useState('{"code":"code","full_name":"full_name","parent_code":"parent_code"}');
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const [pendingDraft, setPendingDraft] = useState({ parentCode: '', fullName: '', adminComment: '' });
  const [pendingNotice, setPendingNotice] = useState('');
  const [pendingError, setPendingError] = useState('');
  const [validateForm, setValidateForm] = useState({ mksOksCode: '', okstuCode: '', udkCode: '' });
  const [validateResult, setValidateResult] = useState<any>(null);
  const [validateNotice, setValidateNotice] = useState('');
  const [validateError, setValidateError] = useState('');

  const [terminologyFilters, setTerminologyFilters] = useState({
    rawTerm: '',
    standardTerm: '',
    termType: '',
    isBlocked: '',
    scope: '',
    page: 1,
    pageSize: 25,
  });
  const [selectedTermId, setSelectedTermId] = useState<string | null>(null);
  const [termDraft, setTermDraft] = useState(initialTermDraft());
  const [termNotice, setTermNotice] = useState('');
  const [termError, setTermError] = useState('');
  const [termDeleteOpen, setTermDeleteOpen] = useState(false);
  const [termImportOpen, setTermImportOpen] = useState(false);
  const [termImportFile, setTermImportFile] = useState<File | null>(null);
  const [termImportMapping, setTermImportMapping] = useState('{"raw_term":"raw_term","standard_term":"standard_term","normalized_value":"normalized_value"}');
  const [normalizeInput, setNormalizeInput] = useState('');
  const [normalizeResult, setNormalizeResult] = useState<any>(null);

  const canEditClassifiers =
    currentRole === 'systemAdmin' || Boolean(currentPermissions.can_manage_registry || currentPermissions.can_manage_classifiers);
  const canEditTerminology =
    currentRole === 'systemAdmin' || Boolean(currentPermissions.can_manage_registry || currentPermissions.can_manage_terminology);
  const canEdit = registryTab === 'terminology' ? canEditTerminology : canEditClassifiers;

  const classifiersListQuery = useQuery({
    queryKey: ['registry-classifiers-list', workMode, classifierSystem, classifierFilters],
    queryFn: () =>
      registryApi.classifiers.list({
        classifierSystem,
        code: classifierFilters.code || undefined,
        fullName: classifierFilters.fullName || undefined,
        status: classifierFilters.status || undefined,
        parentCode: classifierFilters.parentCode || undefined,
        page: classifierFilters.page,
        pageSize: classifierFilters.pageSize,
      }),
    enabled: registryTab === 'classifiers' && classifierView === 'list',
    staleTime: 20_000,
  });

  const classifiersTreeQuery = useQuery({
    queryKey: ['registry-classifiers-tree', workMode, classifierSystem, treeFilters],
    queryFn: () =>
      registryApi.classifiers.tree({
        classifierSystem,
        rootCode: treeFilters.rootCode || undefined,
        maxDepth: treeFilters.maxDepth,
        search: treeFilters.search || undefined,
        status: treeFilters.status || undefined,
      }),
    enabled: registryTab === 'classifiers' && classifierView === 'tree',
    staleTime: 20_000,
  });

  const pendingQuery = useQuery({
    queryKey: ['registry-classifiers-pending', workMode, pendingFilters],
    queryFn: () =>
      registryApi.classifiers.pending({
        system: pendingFilters.system || undefined,
        status: pendingFilters.status || undefined,
        page: pendingFilters.page,
        pageSize: pendingFilters.pageSize,
      }),
    enabled: registryTab === 'classifiers',
    staleTime: 15_000,
  });

  const selectedClassifierQuery = useQuery({
    queryKey: ['registry-classifier-detail', workMode, selectedClassifierKey?.system, selectedClassifierKey?.code],
    queryFn: () => registryApi.classifiers.get(selectedClassifierKey!.code, selectedClassifierKey!.system),
    enabled: registryTab === 'classifiers' && Boolean(selectedClassifierKey) && classifierView !== 'validate',
    staleTime: 30_000,
  });

  const terminologyListQuery = useQuery({
    queryKey: ['registry-terminology-list', workMode, terminologyFilters],
    queryFn: () =>
      registryApi.terminology.list({
        rawTerm: terminologyFilters.rawTerm || undefined,
        standardTerm: terminologyFilters.standardTerm || undefined,
        termType: terminologyFilters.termType || undefined,
        isBlocked: terminologyFilters.isBlocked === '' ? undefined : terminologyFilters.isBlocked === 'true',
        scope: terminologyFilters.scope || undefined,
        page: terminologyFilters.page,
        pageSize: terminologyFilters.pageSize,
      }),
    enabled: true,
    staleTime: 20_000,
  });

  const selectedTermQuery = useQuery({
    queryKey: ['registry-terminology-detail', workMode, selectedTermId],
    queryFn: () => registryApi.terminology.get(selectedTermId!),
    enabled: registryTab === 'terminology' && Boolean(selectedTermId),
    staleTime: 30_000,
  });

  const classifierRows = classifiersListQuery.data?.data ?? [];
  const classifierTreeRoots = classifiersTreeQuery.data?.data ?? [];
  const pendingRows = pendingQuery.data?.data ?? [];
  const terminologyRows = terminologyListQuery.data?.data ?? [];
  const classifierListMeta = classifiersListQuery.data?.meta ?? {};
  const classifierPendingMeta = pendingQuery.data?.meta ?? {};
  const terminologyMeta = terminologyListQuery.data?.meta ?? {};
  const selectedClassifier = selectedClassifierQuery.data ?? null;
  const selectedTerm = selectedTermQuery.data ?? null;

  useEffect(() => {
    if (selectedClassifierKey && selectedClassifier) {
      setClassifierDraft(classifierDraftFromNode(selectedClassifier, classifierSystem));
      return;
    }

    if (!selectedClassifierKey) {
      setClassifierDraft(initialClassifierDraft(classifierSystem));
    }
  }, [classifierSystem, selectedClassifier, selectedClassifierKey]);

  useEffect(() => {
    if (selectedTermId && selectedTerm) {
      setTermDraft(termDraftFromNode(selectedTerm));
      return;
    }

    if (!selectedTermId) {
      setTermDraft(initialTermDraft());
    }
  }, [selectedTerm, selectedTermId]);

  useEffect(() => {
    if (selectedClassifierKey && !classifierRows.some((item) => item.code === selectedClassifierKey.code && item.classifier_system === selectedClassifierKey.system)) {
      setSelectedClassifierKey(null);
    }
  }, [classifierRows, selectedClassifierKey]);

  useEffect(() => {
    if (selectedTermId && !terminologyRows.some((item) => item.id === selectedTermId)) {
      setSelectedTermId(null);
    }
  }, [selectedTermId, terminologyRows]);

  useEffect(() => {
    if (!pendingAction) return;

    setPendingDraft({
      parentCode: pendingAction.item.suggested_parent_code ?? '',
      fullName: pendingAction.item.suggested_parent_name ?? '',
      adminComment: pendingAction.item.admin_comment ?? '',
    });
  }, [pendingAction]);

  const refreshClassifiers = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['registry-classifiers-list'] }),
      queryClient.invalidateQueries({ queryKey: ['registry-classifiers-tree'] }),
      queryClient.invalidateQueries({ queryKey: ['registry-classifiers-pending'] }),
      queryClient.invalidateQueries({ queryKey: ['registry-classifier-detail'] }),
    ]);
  };

  const refreshTerminology = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['registry-terminology-list'] }),
      queryClient.invalidateQueries({ queryKey: ['registry-terminology-detail'] }),
    ]);
  };

  const runClassifierAction = async (action: () => Promise<void>) => {
    setClassifierError('');
    setClassifierNotice('');
    try {
      await action();
    } catch (error: any) {
      setClassifierError(extractApiMessage(error));
    }
  };

  const runTermAction = async (action: () => Promise<void>) => {
    setTermError('');
    setTermNotice('');
    try {
      await action();
    } catch (error: any) {
      setTermError(extractApiMessage(error));
    }
  };

  const classifierStatusLabel = useMemo(() => {
    if (classifiersListQuery.isFetching || classifiersTreeQuery.isFetching || pendingQuery.isFetching) return 'Загрузка данных Registry...';
    if (isDemo) return 'Demo: данные справочников не загружаются с сервера';
    return 'Сервер подключен к редакторам справочников';
  }, [classifiersListQuery.isFetching, classifiersTreeQuery.isFetching, isDemo, pendingQuery.isFetching]);

  const classifierListCount = Number(classifierListMeta?.total ?? classifierRows.length);
  const pendingCount = Number(classifierPendingMeta?.total ?? pendingRows.length);
  const terminologyCount = Number(terminologyMeta?.total ?? terminologyRows.length);

  const handleClassifierSelect = (node: RegistryClassifierNode) => {
    setSelectedClassifierKey({ system: node.classifier_system, code: node.code });
    setClassifierSystem(node.classifier_system || classifierSystem);
  };

  const handleClassifierNew = () => {
    setSelectedClassifierKey(null);
    setClassifierDraft(initialClassifierDraft(classifierSystem));
    setClassifierNotice('Создана пустая форма классификатора.');
    setClassifierError('');
  };

  const handleClassifierSave = async () => {
    if (!canEdit || isDemo) {
      setClassifierError('Редактирование классификаторов доступно только в продуктивном режиме для администратора.');
      return;
    }

    const payload = classifierPayloadFromDraft(classifierDraft);
    if (!payload.code || !payload.full_name) {
      setClassifierError('Нужно заполнить минимум код и наименование.');
      return;
    }

    await runClassifierAction(async () => {
      if (selectedClassifierKey) {
        await registryApi.classifiers.update(selectedClassifierKey.code, selectedClassifierKey.system, payload);
        setClassifierNotice('Классификатор обновлён.');
      } else {
        await registryApi.classifiers.create(payload);
        setClassifierNotice('Классификатор создан.');
      }

      await refreshClassifiers();
      setSelectedClassifierKey(null);
      setClassifierDraft(initialClassifierDraft(classifierDraft.classifierSystem));
    });
  };

  const handleClassifierDelete = async () => {
    if (!selectedClassifierKey || !canEdit || isDemo) return;

    await runClassifierAction(async () => {
      await registryApi.classifiers.delete(selectedClassifierKey.code, selectedClassifierKey.system);
      setClassifierNotice('Классификатор удалён.');
      setClassifierDeleteOpen(false);
      setSelectedClassifierKey(null);
      setClassifierDraft(initialClassifierDraft(classifierDraft.classifierSystem));
      await refreshClassifiers();
    });
  };

  const handleClassifierImport = async () => {
    if (!classifierImportFile || !canEdit || isDemo) {
      setClassifierError('Для импорта нужен файл и продуктивный режим.');
      return;
    }

    await runClassifierAction(async () => {
      await registryApi.classifiers.import(classifierImportFile, classifierSystem, classifierImportMapping);
      setClassifierNotice('Импорт классификаторов отправлен.');
      setClassifierImportOpen(false);
      setClassifierImportFile(null);
      await refreshClassifiers();
    });
  };

  const handlePendingAction = async () => {
    if (!pendingAction || !canEdit || isDemo) {
      setPendingError('Действие по неизвестному коду доступно только в продуктивном режиме для администратора.');
      return;
    }

    await runClassifierAction(async () => {
      if (pendingAction.mode === 'accept') {
        await registryApi.classifiers.acceptPending(pendingAction.item.id, {
          parentCode: pendingDraft.parentCode || undefined,
          fullName: pendingDraft.fullName || undefined,
          adminComment: pendingDraft.adminComment || undefined,
        });
        setPendingNotice('Неизвестный код принят.');
      } else {
        await registryApi.classifiers.rejectPending(pendingAction.item.id, pendingDraft.adminComment || undefined);
        setPendingNotice('Неизвестный код отклонён.');
      }

      setPendingAction(null);
      setPendingDraft({ parentCode: '', fullName: '', adminComment: '' });
      await refreshClassifiers();
    });
  };

  const handleValidateClassification = async () => {
    if (isDemo) {
      setValidateError('Проверка классификации доступна в продуктивном режиме.');
      return;
    }

    setValidateError('');
    setValidateNotice('');
    try {
      const result = await registryApi.classifiers.validate({
        mksOksCode: validateForm.mksOksCode || undefined,
        okstuCode: validateForm.okstuCode || undefined,
        udkCode: validateForm.udkCode || undefined,
      });
      setValidateResult(result);
      setValidateNotice('Проверка классификации выполнена.');
    } catch (error: any) {
      setValidateError(extractApiMessage(error));
    }
  };

  const handleTermSelect = (item: RegistryTerminologyEntry) => {
    setSelectedTermId(item.id);
  };

  const handleTermNew = () => {
    setSelectedTermId(null);
    setTermDraft(initialTermDraft());
    setTermNotice('Создана пустая форма термина.');
    setTermError('');
  };

  const handleTermSave = async () => {
    if (!canEdit || isDemo) {
      setTermError('Редактирование терминологии доступно только в продуктивном режиме для администратора.');
      return;
    }

    const payload = termPayloadFromDraft(termDraft);
    if (!payload.raw_term || !payload.standard_term || !payload.normalized_value) {
      setTermError('Нужно заполнить raw_term, standard_term и normalized_value.');
      return;
    }

    await runTermAction(async () => {
      if (selectedTermId) {
        await registryApi.terminology.update(selectedTermId, payload);
        setTermNotice('Термин обновлён.');
      } else {
        await registryApi.terminology.create(payload);
        setTermNotice('Термин создан.');
      }

      await refreshTerminology();
      setSelectedTermId(null);
      setTermDraft(initialTermDraft());
    });
  };

  const handleTermDelete = async () => {
    if (!selectedTermId || !canEdit || isDemo) return;

    await runTermAction(async () => {
      await registryApi.terminology.delete(selectedTermId);
      setTermNotice('Термин удалён.');
      setTermDeleteOpen(false);
      setSelectedTermId(null);
      setTermDraft(initialTermDraft());
      await refreshTerminology();
    });
  };

  const handleTermImport = async () => {
    if (!termImportFile || !canEdit || isDemo) {
      setTermError('Для импорта нужен файл и продуктивный режим.');
      return;
    }

    await runTermAction(async () => {
      await registryApi.terminology.import(termImportFile, termImportMapping);
      setTermNotice('Импорт терминологии отправлен.');
      setTermImportOpen(false);
      setTermImportFile(null);
      await refreshTerminology();
    });
  };

  const handleNormalizeTerm = async () => {
    if (!normalizeInput.trim()) return;
    if (isDemo) {
      setNormalizeResult({
        raw_term: normalizeInput,
        standard_term: normalizeInput,
        normalized_value: normalizeInput.toLowerCase(),
        term_type: 'unknown',
        is_blocked: false,
      });
      return;
    }

    try {
      const result = await registryApi.terminology.normalize(normalizeInput.trim());
      setNormalizeResult(result);
    } catch (error: any) {
      setNormalizeResult(null);
      setTermError(extractApiMessage(error));
    }
  };

  const renderClassifierEditor = () => {
    const selectedLabel = selectedClassifierKey ? `${selectedClassifierKey.system} · ${selectedClassifierKey.code}` : 'Новый классификатор';
    const listLoading = classifiersListQuery.isLoading || classifiersListQuery.isFetching;
    const treeLoading = classifiersTreeQuery.isLoading || classifiersTreeQuery.isFetching;
    const pendingLoading = pendingQuery.isLoading || pendingQuery.isFetching;

    if (classifierView === 'validate') {
      return (
        <Paper variant="outlined" sx={{ p: 2, ...panelSx(isLight) }}>
          <Stack spacing={2}>
            <Box sx={sectionHeaderSx(isLight)}>
              <Typography sx={{ fontWeight: 600 }}>Проверка классификации</Typography>
              <Typography variant="caption" color="text.secondary">
                Запрос к `POST /registry/classifiers/validate`
              </Typography>
            </Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 1.2 }}>
              <TextField
                label="mks_oks_code"
                value={validateForm.mksOksCode}
                onChange={(event) => setValidateForm((current) => ({ ...current, mksOksCode: event.target.value }))}
                size="small"
              />
              <TextField
                label="okstu_code"
                value={validateForm.okstuCode}
                onChange={(event) => setValidateForm((current) => ({ ...current, okstuCode: event.target.value }))}
                size="small"
              />
              <TextField
                label="udk_code"
                value={validateForm.udkCode}
                onChange={(event) => setValidateForm((current) => ({ ...current, udkCode: event.target.value }))}
                size="small"
              />
            </Box>
            <Stack direction="row" spacing={1}>
              <Button variant="contained" onClick={() => void handleValidateClassification()} startIcon={<FlaskConical size={16} />}>
                Проверить
              </Button>
              <Button variant="outlined" onClick={() => setValidateForm({ mksOksCode: '', okstuCode: '', udkCode: '' })}>
                Очистить
              </Button>
            </Stack>
            {validateError && <Alert severity="error">{validateError}</Alert>}
            {validateNotice && <Alert severity="success">{validateNotice}</Alert>}
            {validateResult && (
              <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.025)' }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Результат
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 1 }}>
                  {Object.entries(validateResult.classification ?? validateResult).map(([key, value]) => (
                    <Box key={key}>
                      <Typography variant="caption" color="text.secondary">
                        {key}
                      </Typography>
                      <Typography sx={{ fontWeight: 520, overflowWrap: 'anywhere' }}>
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Paper>
            )}
          </Stack>
        </Paper>
      );
    }

    if (classifierView === 'pending') {
      const selectedPending = pendingAction?.item ?? pendingRows[0] ?? null;

      return (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1.3fr 0.9fr' }, gap: 2 }}>
          <Paper variant="outlined" sx={{ p: 2, ...panelSx(isLight) }}>
            <Stack spacing={1.5}>
              <Box sx={sectionHeaderSx(isLight)}>
                <Typography sx={{ fontWeight: 600 }}>Неизвестные коды</Typography>
                <Typography variant="caption" color="text.secondary">
                  Фильтры вынесены в верхнюю строку, здесь остается только обработка.
                </Typography>
              </Box>

              {pendingError && <Alert severity="error">{pendingError}</Alert>}
              {pendingNotice && <Alert severity="success">{pendingNotice}</Alert>}

              <TableContainer component={Paper} variant="outlined" sx={panelSx(isLight)}>
                <Table size="small" sx={tableSx}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Код</TableCell>
                      <TableCell>Документ</TableCell>
                      <TableCell>Предложение</TableCell>
                      <TableCell>Статус</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pendingLoading ? (
                      <TableRow>
                        <TableCell colSpan={4} sx={{ py: 3, textAlign: 'center' }}>
                          Загрузка...
                        </TableCell>
                      </TableRow>
                    ) : pendingRows.length ? (
                      pendingRows.map((item) => (
                        <TableRow
                          key={item.id}
                          hover
                          onClick={() =>
                            setPendingAction({
                              mode: pendingAction?.item.id === item.id ? pendingAction.mode : 'accept',
                              item,
                            })
                          }
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell sx={{ whiteSpace: 'nowrap' }}>{item.code}</TableCell>
                          <TableCell>
                            <Typography sx={{ fontWeight: 520 }}>{item.found_in_document_title}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {item.system} · {item.found_in_document_id}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography>{item.suggested_parent_name ?? '—'}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {item.suggested_parent_code ?? 'без подсказки'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip size="small" variant="outlined" label={item.status} />
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={4} sx={{ py: 3, textAlign: 'center', color: 'text.secondary' }}>
                          Нет неизвестных кодов.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Stack>
          </Paper>

          <Paper variant="outlined" sx={{ p: 2, ...panelSx(isLight) }}>
            <Stack spacing={1.5}>
              <Box sx={sectionHeaderSx(isLight)}>
                <Typography sx={{ fontWeight: 600 }}>Панель обработки</Typography>
                <Typography variant="caption" color="text.secondary">
                  Коды связаны с классификатором. Можно обрабатывать в одной форме.
                </Typography>
              </Box>
              {selectedPending ? (
                <>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Код
                    </Typography>
                    <Typography sx={{ fontWeight: 600 }}>{selectedPending.code}</Typography>
                  </Box>
                  <TextField
                    label="parent_code"
                    size="small"
                    value={pendingDraft.parentCode}
                    onChange={(event) => setPendingDraft((current) => ({ ...current, parentCode: event.target.value }))}
                  />
                  <TextField
                    label="full_name"
                    size="small"
                    value={pendingDraft.fullName}
                    onChange={(event) => setPendingDraft((current) => ({ ...current, fullName: event.target.value }))}
                  />
                  <TextField
                    label="admin_comment"
                    size="small"
                    multiline
                    minRows={3}
                    value={pendingDraft.adminComment}
                    onChange={(event) => setPendingDraft((current) => ({ ...current, adminComment: event.target.value }))}
                  />
                  <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                    <Button
                      variant="contained"
                      onClick={() =>
                        setPendingAction({
                          mode: 'accept',
                          item: selectedPending,
                        })
                      }
                      startIcon={<CheckCircle2 size={16} />}
                    >
                      Принять
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={() =>
                        setPendingAction({
                          mode: 'reject',
                          item: selectedPending,
                        })
                      }
                      startIcon={<X size={16} />}
                    >
                      Отклонить
                    </Button>
                  </Stack>
                  <Divider />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Подсказка
                    </Typography>
                    <Typography sx={{ whiteSpace: 'pre-wrap' }}>
                      {selectedPending.suggested_parent_name ?? 'Подсказка отсутствует'}
                    </Typography>
                  </Box>
                </>
              ) : (
                <Alert severity="info">Выберите код в таблице.</Alert>
              )}
            </Stack>
          </Paper>
        </Box>
      );
    }

    const rows = classifiersListQuery.data?.data ?? [];

    const treeSection = (
      <Paper variant="outlined" sx={{ p: 2, ...panelSx(isLight), height: '100%', overflow: 'hidden' }}>
        <Stack spacing={1.5} sx={{ height: '100%' }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.1} sx={{ ...sectionHeaderSx(isLight), alignItems: { xs: 'stretch', md: 'center' } }}>
            <Typography sx={{ flex: 1, fontWeight: 600 }}>
              {classifierView === 'tree' ? 'Дерево классификаторов' : 'Список классификаторов'}
            </Typography>
            <TextField
              select
              size="small"
              label="Система"
              value={classifierSystem}
              onChange={(event) => {
                setClassifierSystem(event.target.value);
                setClassifierDraft((current) => ({ ...current, classifierSystem: event.target.value }));
              }}
              sx={{ minWidth: 140 }}
            >
              {CLASSIFIER_SYSTEM_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <Button variant="outlined" startIcon={<Plus size={15} />} onClick={handleClassifierNew} disabled={!canEdit || isDemo}>
              Новый
            </Button>
            <Button variant="outlined" startIcon={<Upload size={15} />} onClick={() => setClassifierImportOpen(true)} disabled={!canEdit || isDemo}>
              Импорт
            </Button>
            <Button variant="outlined" startIcon={<RefreshCw size={15} />} onClick={() => void refreshClassifiers()}>
              Обновить
            </Button>
          </Stack>

          {classifierError && <Alert severity="error">{classifierError}</Alert>}
          {classifierNotice && <Alert severity="success">{classifierNotice}</Alert>}
          {isDemo && <Alert severity="info">Редактор работает в продуктивном режиме. В demo данные справочников не подгружаются.</Alert>}

          {classifierView === 'tree' ? (
            <Stack spacing={1} sx={{ flex: 1, overflow: 'auto', pr: 0.5 }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 1 }}>
                <TextField
                  label="root_code"
                  size="small"
                  value={treeFilters.rootCode}
                  onChange={(event) => setTreeFilters((current) => ({ ...current, rootCode: event.target.value }))}
                />
                <TextField
                  label="search"
                  size="small"
                  value={treeFilters.search}
                  onChange={(event) => setTreeFilters((current) => ({ ...current, search: event.target.value }))}
                />
                <TextField
                  select
                  label="status"
                  size="small"
                  value={treeFilters.status}
                  onChange={(event) => setTreeFilters((current) => ({ ...current, status: event.target.value }))}
                >
                  <MenuItem value="">Все</MenuItem>
                  {CLASSIFIER_STATUS_OPTIONS.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  label="max_depth"
                  size="small"
                  type="number"
                  value={treeFilters.maxDepth}
                  onChange={(event) =>
                    setTreeFilters((current) => ({ ...current, maxDepth: Number(event.target.value) || 10 }))
                  }
                />
              </Box>

              {treeLoading ? (
                <Alert severity="info">Загрузка дерева...</Alert>
              ) : classifierTreeRoots.length ? (
                <Box sx={{ overflow: 'auto', pr: 0.5 }}>
                  {classifierTreeRoots.map((node) => (
                    <TreeNode
                      key={`${node.classifier_system}-${node.code}`}
                      node={node}
                      depth={0}
                      selectedCode={selectedClassifierKey?.code}
                      onSelect={handleClassifierSelect}
                    />
                  ))}
                </Box>
              ) : (
                <Alert severity="info">Дерево пустое.</Alert>
              )}
            </Stack>
          ) : (
            <Stack spacing={1} sx={{ flex: 1, overflow: 'hidden' }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 1 }}>
                <TextField
                  label="code"
                  size="small"
                  value={classifierFilters.code}
                  onChange={(event) => setClassifierFilters((current) => ({ ...current, code: event.target.value }))}
                />
                <TextField
                  label="full_name"
                  size="small"
                  value={classifierFilters.fullName}
                  onChange={(event) => setClassifierFilters((current) => ({ ...current, fullName: event.target.value }))}
                />
                <TextField
                  label="parent_code"
                  size="small"
                  value={classifierFilters.parentCode}
                  onChange={(event) => setClassifierFilters((current) => ({ ...current, parentCode: event.target.value }))}
                />
                <TextField
                  select
                  label="status"
                  size="small"
                  value={classifierFilters.status}
                  onChange={(event) => setClassifierFilters((current) => ({ ...current, status: event.target.value }))}
                >
                  <MenuItem value="">Все</MenuItem>
                  {CLASSIFIER_STATUS_OPTIONS.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </TextField>
              </Box>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 1 }}>
                <TextField
                  label="page"
                  size="small"
                  type="number"
                  value={classifierFilters.page}
                  onChange={(event) => setClassifierFilters((current) => ({ ...current, page: Number(event.target.value) || 1 }))}
                />
                <TextField
                  label="page_size"
                  size="small"
                  type="number"
                  value={classifierFilters.pageSize}
                  onChange={(event) => setClassifierFilters((current) => ({ ...current, pageSize: Number(event.target.value) || 25 }))}
                />
              </Box>

              <TableContainer component={Paper} variant="outlined" sx={{ flex: 1, ...panelSx(isLight) }}>
                <Table size="small" sx={tableSx}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Код</TableCell>
                      <TableCell>Наименование</TableCell>
                      <TableCell>Родитель</TableCell>
                      <TableCell>Статус</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {listLoading ? (
                      <TableRow>
                        <TableCell colSpan={4} sx={{ py: 3, textAlign: 'center' }}>
                          Загрузка...
                        </TableCell>
                      </TableRow>
                    ) : rows.length ? (
                      rows.map((node) => {
                        const selected = selectedClassifierKey?.system === node.classifier_system && selectedClassifierKey?.code === node.code;

                        return (
                          <TableRow
                            key={`${node.classifier_system}-${node.code}`}
                            hover
                            onClick={() => handleClassifierSelect(node)}
                            sx={{
                              cursor: 'pointer',
                              bgcolor: selected ? 'rgba(152, 217, 216, 0.08) !important' : undefined,
                            }}
                          >
                            <TableCell>{node.code}</TableCell>
                            <TableCell>
                              <Typography sx={{ fontWeight: 520 }}>{node.full_name}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {node.classifier_system}
                              </Typography>
                            </TableCell>
                            <TableCell>{node.parent_code ?? '—'}</TableCell>
                            <TableCell>
                              <Chip size="small" variant="outlined" label={node.status} />
                            </TableCell>
                          </TableRow>
                        );
                      })
                    ) : (
                      <TableRow>
                        <TableCell colSpan={4} sx={{ py: 3, textAlign: 'center', color: 'text.secondary' }}>
                          Ничего не найдено.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              <Typography variant="caption" color="text.secondary">
                Всего: {classifierListCount}
              </Typography>
            </Stack>
          )}
        </Stack>
      </Paper>
    );

    const editorSection = (
      <Paper variant="outlined" sx={{ p: 2, ...panelSx(isLight), height: '100%' }}>
        <Stack spacing={1.5} sx={{ height: '100%' }}>
          <Box sx={sectionHeaderSx(isLight)}>
            <Typography sx={{ fontWeight: 600 }}>{selectedLabel}</Typography>
            <Typography variant="caption" color="text.secondary">
              {selectedClassifier ? 'Редактирование выбранного узла' : 'Создание нового узла'}
            </Typography>
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 1 }}>
            <TextField
              select
              label="classifier_system"
              size="small"
              value={classifierDraft.classifierSystem}
              onChange={(event) =>
                setClassifierDraft((current) => ({ ...current, classifierSystem: event.target.value }))
              }
              disabled={!canEdit || isDemo}
            >
              {CLASSIFIER_SYSTEM_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="code"
              size="small"
              value={classifierDraft.code}
              onChange={(event) => setClassifierDraft((current) => ({ ...current, code: event.target.value }))}
              disabled={!canEdit || isDemo}
            />
            <TextField
              label="parent_code"
              size="small"
              value={classifierDraft.parentCode}
              onChange={(event) => setClassifierDraft((current) => ({ ...current, parentCode: event.target.value }))}
              disabled={!canEdit || isDemo}
            />
            <TextField
              select
              label="status"
              size="small"
              value={classifierDraft.status}
              onChange={(event) => setClassifierDraft((current) => ({ ...current, status: event.target.value }))}
              disabled={!canEdit || isDemo}
            >
              {CLASSIFIER_STATUS_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="effective_date"
              size="small"
              value={classifierDraft.effectiveDate}
              onChange={(event) => setClassifierDraft((current) => ({ ...current, effectiveDate: event.target.value }))}
              disabled={!canEdit || isDemo}
            />
            <TextField
              label="replaced_by"
              size="small"
              value={classifierDraft.replacedBy}
              onChange={(event) => setClassifierDraft((current) => ({ ...current, replacedBy: event.target.value }))}
              disabled={!canEdit || isDemo}
            />
          </Box>

          <TextField
            label="full_name"
            size="small"
            multiline
            minRows={3}
            value={classifierDraft.fullName}
            onChange={(event) => setClassifierDraft((current) => ({ ...current, fullName: event.target.value }))}
            disabled={!canEdit || isDemo}
          />

          <Divider />
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
            <Button variant="contained" onClick={() => void handleClassifierSave()} startIcon={<Save size={16} />} disabled={!canEdit || isDemo}>
              Сохранить
            </Button>
            <Button variant="outlined" onClick={() => setClassifierDraft(initialClassifierDraft(classifierSystem))} disabled={!canEdit || isDemo}>
              Сбросить
            </Button>
            <Button
              variant="outlined"
              color="error"
              onClick={() => setClassifierDeleteOpen(true)}
              disabled={!canEdit || isDemo || !selectedClassifierKey}
              startIcon={<Trash2 size={16} />}
            >
              Удалить
            </Button>
          </Stack>

          <Box sx={{ mt: 'auto' }}>
            <Typography variant="caption" color="text.secondary">
              {classifierStatusLabel}
            </Typography>
          </Box>
        </Stack>
      </Paper>
    );

    if (classifierView === 'tree') {
      return (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1.35fr) minmax(320px, 0.75fr)' }, gap: 2 }}>
          {treeSection}
          {editorSection}
        </Box>
      );
    }

    return (
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1.35fr) minmax(320px, 0.75fr)' }, gap: 2 }}>
        {treeSection}
        {editorSection}
      </Box>
    );
  };

  const renderTerminologyEditor = () => {
    const listLoading = terminologyListQuery.isLoading || terminologyListQuery.isFetching;

    return (
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'minmax(0, 1.35fr) minmax(320px, 0.75fr)' }, gap: 2 }}>
        <Paper variant="outlined" sx={{ p: 2, ...panelSx(isLight), height: '100%' }}>
          <Stack spacing={1.5} sx={{ height: '100%' }}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.1} sx={{ ...sectionHeaderSx(isLight), alignItems: { xs: 'stretch', md: 'center' } }}>
              <Typography sx={{ flex: 1, fontWeight: 600 }}>Терминология</Typography>
              <Button variant="outlined" startIcon={<Plus size={15} />} onClick={handleTermNew} disabled={!canEdit || isDemo}>
                Новый
              </Button>
              <Button variant="outlined" startIcon={<Upload size={15} />} onClick={() => setTermImportOpen(true)} disabled={!canEdit || isDemo}>
                Импорт
              </Button>
              <Button variant="outlined" startIcon={<RefreshCw size={15} />} onClick={() => void refreshTerminology()}>
                Обновить
              </Button>
            </Stack>

            {termError && <Alert severity="error">{termError}</Alert>}
            {termNotice && <Alert severity="success">{termNotice}</Alert>}
            {isDemo && <Alert severity="info">Редактор работает в продуктивном режиме. В demo терминология не подгружается.</Alert>}

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 1 }}>
              <TextField
                label="raw_term"
                size="small"
                value={terminologyFilters.rawTerm}
                onChange={(event) => setTerminologyFilters((current) => ({ ...current, rawTerm: event.target.value }))}
              />
              <TextField
                label="standard_term"
                size="small"
                value={terminologyFilters.standardTerm}
                onChange={(event) => setTerminologyFilters((current) => ({ ...current, standardTerm: event.target.value }))}
              />
              <TextField
                select
                label="term_type"
                size="small"
                value={terminologyFilters.termType}
                onChange={(event) => setTerminologyFilters((current) => ({ ...current, termType: event.target.value }))}
              >
                <MenuItem value="">Все</MenuItem>
                {TERMINOLOGY_TYPE_OPTIONS.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </TextField>
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 1 }}>
              <TextField
                select
                label="is_blocked"
                size="small"
                value={terminologyFilters.isBlocked}
                onChange={(event) => setTerminologyFilters((current) => ({ ...current, isBlocked: event.target.value }))}
              >
                <MenuItem value="">Все</MenuItem>
                <MenuItem value="true">Да</MenuItem>
                <MenuItem value="false">Нет</MenuItem>
              </TextField>
              <TextField
                label="scope"
                size="small"
                value={terminologyFilters.scope}
                onChange={(event) => setTerminologyFilters((current) => ({ ...current, scope: event.target.value }))}
              />
              <TextField
                label="page_size"
                size="small"
                type="number"
                value={terminologyFilters.pageSize}
                onChange={(event) =>
                  setTerminologyFilters((current) => ({ ...current, pageSize: Number(event.target.value) || 25 }))
                }
              />
            </Box>

            <TableContainer component={Paper} variant="outlined" sx={{ flex: 1, ...panelSx(isLight) }}>
              <Table size="small" sx={tableSx}>
                <TableHead>
                  <TableRow>
                    <TableCell>Термин</TableCell>
                    <TableCell>Эталон</TableCell>
                    <TableCell>Тип</TableCell>
                    <TableCell>Блок</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {listLoading ? (
                    <TableRow>
                      <TableCell colSpan={4} sx={{ py: 3, textAlign: 'center' }}>
                        Загрузка...
                      </TableCell>
                    </TableRow>
                  ) : terminologyRows.length ? (
                    terminologyRows.map((item) => {
                      const selected = selectedTermId === item.id;

                      return (
                        <TableRow
                          key={item.id}
                          hover
                          onClick={() => handleTermSelect(item)}
                          sx={{
                            cursor: 'pointer',
                            bgcolor: selected ? 'rgba(152, 217, 216, 0.08) !important' : undefined,
                          }}
                        >
                          <TableCell>
                            <Typography sx={{ fontWeight: 520 }}>{item.raw_term}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {item.normalized_value}
                            </Typography>
                          </TableCell>
                          <TableCell>{item.standard_term}</TableCell>
                          <TableCell>{item.term_type}</TableCell>
                          <TableCell>
                            <Chip size="small" label={item.is_blocked ? 'Да' : 'Нет'} variant="outlined" />
                          </TableCell>
                        </TableRow>
                      );
                    })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={4} sx={{ py: 3, textAlign: 'center', color: 'text.secondary' }}>
                        Ничего не найдено.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <Typography variant="caption" color="text.secondary">
              Всего: {terminologyCount}
            </Typography>
          </Stack>
        </Paper>

        <Paper variant="outlined" sx={{ p: 2, ...panelSx(isLight), height: '100%' }}>
          <Stack spacing={1.5} sx={{ height: '100%' }}>
            <Box sx={sectionHeaderSx(isLight)}>
              <Typography sx={{ fontWeight: 600 }}>
                {selectedTermId ? `Термин ${selectedTermId}` : 'Новый термин'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Редактирование, нормализация и массивы через теги
              </Typography>
            </Box>

            <TextField
              label="raw_term"
              size="small"
              value={termDraft.rawTerm}
              onChange={(event) => setTermDraft((current) => ({ ...current, rawTerm: event.target.value }))}
              disabled={!canEdit || isDemo}
            />
            <TextField
              label="standard_term"
              size="small"
              value={termDraft.standardTerm}
              onChange={(event) => setTermDraft((current) => ({ ...current, standardTerm: event.target.value }))}
              disabled={!canEdit || isDemo}
            />
            <TextField
              label="normalized_value"
              size="small"
              value={termDraft.normalizedValue}
              onChange={(event) => setTermDraft((current) => ({ ...current, normalizedValue: event.target.value }))}
              disabled={!canEdit || isDemo}
            />
            <TextField
              select
              label="term_type"
              size="small"
              value={termDraft.termType}
              onChange={(event) => setTermDraft((current) => ({ ...current, termType: event.target.value }))}
              disabled={!canEdit || isDemo}
            >
              {TERMINOLOGY_TYPE_OPTIONS.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>

            <FormControlLabel
              control={
                <Switch
                  checked={termDraft.isCaseSensitive}
                  onChange={(event) => setTermDraft((current) => ({ ...current, isCaseSensitive: event.target.checked }))}
                  disabled={!canEdit || isDemo}
                />
              }
              label="is_case_sensitive"
            />

            <TextField
              label="definition"
              size="small"
              multiline
              minRows={3}
              value={termDraft.definition}
              onChange={(event) => setTermDraft((current) => ({ ...current, definition: event.target.value }))}
              disabled={!canEdit || isDemo}
            />

            <TagField
              label="synonyms"
              values={termDraft.synonyms}
              onChange={(values) => setTermDraft((current) => ({ ...current, synonyms: values }))}
              placeholder="Добавить синоним"
              disabled={!canEdit || isDemo}
            />
            <TagField
              label="related_docs"
              values={termDraft.relatedDocs}
              onChange={(values) => setTermDraft((current) => ({ ...current, relatedDocs: values }))}
              placeholder="Добавить документ"
              disabled={!canEdit || isDemo}
            />
            <TagField
              label="scope"
              values={termDraft.scope}
              onChange={(values) => setTermDraft((current) => ({ ...current, scope: values }))}
              placeholder="Добавить область"
              disabled={!canEdit || isDemo}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={termDraft.isBlocked}
                  onChange={(event) => setTermDraft((current) => ({ ...current, isBlocked: event.target.checked }))}
                  disabled={!canEdit || isDemo}
                />
              }
              label="is_blocked"
            />

            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
              <Button variant="contained" onClick={() => void handleTermSave()} startIcon={<Save size={16} />} disabled={!canEdit || isDemo}>
                Сохранить
              </Button>
              <Button variant="outlined" onClick={() => setTermDraft(initialTermDraft())} disabled={!canEdit || isDemo}>
                Сбросить
              </Button>
              <Button
                variant="outlined"
                color="error"
                onClick={() => setTermDeleteOpen(true)}
                disabled={!canEdit || isDemo || !selectedTermId}
                startIcon={<Trash2 size={16} />}
              >
                Удалить
              </Button>
            </Stack>

            <Divider />
            <Stack spacing={1}>
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <TextField
                  fullWidth
                  size="small"
                  label="Проверка нормализации"
                  value={normalizeInput}
                  onChange={(event) => setNormalizeInput(event.target.value)}
                  disabled={!canEdit || isDemo}
                />
                <Button variant="outlined" onClick={() => void handleNormalizeTerm()} disabled={!canEdit || isDemo}>
                  Проверить
                </Button>
              </Stack>
              {normalizeResult && (
                <Paper variant="outlined" sx={{ p: 1.3, bgcolor: 'rgba(255,255,255,0.025)' }}>
                  <Typography variant="subtitle2" sx={{ mb: 0.8 }}>
                    Результат нормализации
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                    {['raw_term', 'standard_term', 'normalized_value', 'term_type', 'is_blocked'].map((key) => (
                      <Box key={key}>
                        <Typography variant="caption" color="text.secondary">
                          {key}
                        </Typography>
                        <Typography sx={{ fontWeight: 520 }}>{String(normalizeResult?.[key] ?? '—')}</Typography>
                      </Box>
                    ))}
                  </Box>
                </Paper>
              )}
            </Stack>
          </Stack>
        </Paper>
      </Box>
    );
  };

  return (
    <Stack spacing={2.1}>
      <Paper variant="outlined" sx={{ p: 2, ...panelSx(isLight) }}>
        <Stack spacing={1}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.2} sx={{ ...sectionHeaderSx(isLight), alignItems: { xs: 'stretch', md: 'center' } }}>
            <Box sx={{ flex: 1 }}>
              <Typography sx={{ fontWeight: 650 }}>Справочники НСИ</Typography>
              <Typography variant="caption" color="text.secondary">
                Классификаторы и терминология Registry Service
              </Typography>
            </Box>
            <Chip
              icon={<FileText size={15} />}
              variant="outlined"
              label={classifierStatusLabel}
              sx={{ alignSelf: { xs: 'flex-start', md: 'center' } }}
            />
          </Stack>
          {classifierError && registryTab === 'classifiers' && <Alert severity="error">{classifierError}</Alert>}
          {classifierNotice && registryTab === 'classifiers' && <Alert severity="success">{classifierNotice}</Alert>}
          {termError && registryTab === 'terminology' && <Alert severity="error">{termError}</Alert>}
          {termNotice && registryTab === 'terminology' && <Alert severity="success">{termNotice}</Alert>}
          {isDemo && <Alert severity="info">Режим demo не содержит реальных данных Registry. Для проверки нужен продуктивный режим.</Alert>}
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 1.2, ...panelSx(isLight) }}>
        <Tabs
          value={registryTab}
          onChange={(_, value) => setRegistryTab(value as RegistryTab)}
          textColor="inherit"
          indicatorColor="primary"
          sx={{ minHeight: 42, '& .MuiTab-root': { minHeight: 42, textTransform: 'none', fontWeight: 560 } }}
        >
          <Tab value="classifiers" label={`Классификаторы (${classifierListCount + pendingCount})`} onClick={() => setRegistryTab('classifiers')} />
          <Tab value="terminology" label={`Терминология (${terminologyCount})`} onClick={() => setRegistryTab('terminology')} />
        </Tabs>
      </Paper>

      {registryTab === 'classifiers' && (
        <Paper variant="outlined" sx={{ p: 1.2, ...panelSx(isLight) }}>
          <Stack spacing={1}>
            <Tabs
              value={classifierView}
              onChange={(_, value) => setClassifierView(value as ClassifierView)}
              textColor="inherit"
              indicatorColor="primary"
              sx={{ minHeight: 40, '& .MuiTab-root': { minHeight: 40, textTransform: 'none' } }}
            >
              <Tab value="list" label={`Список (${classifierListCount})`} onClick={() => setClassifierView('list')} />
              <Tab value="tree" label="Дерево" onClick={() => setClassifierView('tree')} />
              <Tab value="pending" label={`Неизвестные коды (${pendingCount})`} onClick={() => setClassifierView('pending')} />
              <Tab value="validate" label="Проверка" onClick={() => setClassifierView('validate')} />
            </Tabs>

            {classifierView === 'pending' && (
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 1 }}>
                <TextField
                  select
                  size="small"
                  label="system"
                  value={pendingFilters.system}
                  onChange={(event) => setPendingFilters((current) => ({ ...current, system: event.target.value }))}
                >
                  {CLASSIFIER_SYSTEM_OPTIONS.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  select
                  size="small"
                  label="status"
                  value={pendingFilters.status}
                  onChange={(event) => setPendingFilters((current) => ({ ...current, status: event.target.value }))}
                >
                  <MenuItem value="">Все</MenuItem>
                  {PENDING_STATUS_OPTIONS.map((option) => (
                    <MenuItem key={option} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  size="small"
                  label="page"
                  type="number"
                  value={pendingFilters.page}
                  onChange={(event) => setPendingFilters((current) => ({ ...current, page: Number(event.target.value) || 1 }))}
                />
                <TextField
                  size="small"
                  label="page_size"
                  type="number"
                  value={pendingFilters.pageSize}
                  onChange={(event) =>
                    setPendingFilters((current) => ({ ...current, pageSize: Number(event.target.value) || 25 }))
                  }
                />
                <Button
                  variant="outlined"
                  startIcon={<RefreshCw size={15} />}
                  onClick={() => void refreshClassifiers()}
                  sx={{ alignSelf: 'center', justifySelf: { md: 'start' } }}
                >
                  Обновить
                </Button>
              </Box>
            )}

            <Divider />
            {classifierView === 'pending' ? (
              <Stack spacing={2}>{renderClassifierEditor()}</Stack>
            ) : (
              renderClassifierEditor()
            )}
          </Stack>
        </Paper>
      )}

      {registryTab === 'terminology' && (
        <Paper variant="outlined" sx={{ p: 1.2, ...panelSx(isLight) }}>
          <Stack spacing={1}>
            {renderTerminologyEditor()}
          </Stack>
        </Paper>
      )}

      <Dialog open={classifierDeleteOpen} onClose={() => setClassifierDeleteOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Удалить классификатор?</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary">
            Действие необратимо. Если у узла есть дочерние элементы или документы, backend может вернуть ошибку.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClassifierDeleteOpen(false)}>Отмена</Button>
          <Button color="error" variant="contained" onClick={() => void handleClassifierDelete()} startIcon={<Trash2 size={15} />}>
            Удалить
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={termDeleteOpen} onClose={() => setTermDeleteOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Удалить термин?</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary">
            Действие необратимо.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTermDeleteOpen(false)}>Отмена</Button>
          <Button color="error" variant="contained" onClick={() => void handleTermDelete()} startIcon={<Trash2 size={15} />}>
            Удалить
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={classifierImportOpen} onClose={() => setClassifierImportOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Импорт классификаторов</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.6, pt: 1 }}>
          <Button variant="outlined" component="label" startIcon={<Upload size={15} />}>
            {classifierImportFile ? 'Файл выбран' : 'Выбрать файл'}
            <input
              hidden
              type="file"
              accept=".xlsx,.csv"
              onChange={(event) => setClassifierImportFile(event.target.files?.[0] ?? null)}
            />
          </Button>
          {classifierImportFile && (
            <Typography variant="caption" color="text.secondary">
              {classifierImportFile.name}
            </Typography>
          )}
          <TextField
            label="classifier_system"
            select
            size="small"
            value={classifierSystem}
            onChange={(event) => setClassifierSystem(event.target.value)}
          >
            {CLASSIFIER_SYSTEM_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="mapping"
            multiline
            minRows={5}
            value={classifierImportMapping}
            onChange={(event) => setClassifierImportMapping(event.target.value)}
            helperText="JSON-маппинг колонок"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClassifierImportOpen(false)}>Отмена</Button>
          <Button variant="contained" onClick={() => void handleClassifierImport()} startIcon={<Upload size={15} />}>
            Импортировать
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={termImportOpen} onClose={() => setTermImportOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Импорт терминологии</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.6, pt: 1 }}>
          <Button variant="outlined" component="label" startIcon={<Upload size={15} />}>
            {termImportFile ? 'Файл выбран' : 'Выбрать файл'}
            <input hidden type="file" accept=".xlsx,.csv" onChange={(event) => setTermImportFile(event.target.files?.[0] ?? null)} />
          </Button>
          {termImportFile && (
            <Typography variant="caption" color="text.secondary">
              {termImportFile.name}
            </Typography>
          )}
          <TextField
            label="mapping"
            multiline
            minRows={5}
            value={termImportMapping}
            onChange={(event) => setTermImportMapping(event.target.value)}
            helperText="JSON-маппинг колонок"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTermImportOpen(false)}>Отмена</Button>
          <Button variant="contained" onClick={() => void handleTermImport()} startIcon={<Upload size={15} />}>
            Импортировать
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(pendingAction)} onClose={() => setPendingAction(null)} maxWidth="sm" fullWidth>
        <DialogTitle>{pendingAction?.mode === 'accept' ? 'Принять неизвестный код' : 'Отклонить неизвестный код'}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.4, pt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {pendingAction?.item.code}
          </Typography>
          {pendingAction?.mode === 'accept' && (
            <>
              <TextField
                label="parent_code"
                size="small"
                value={pendingDraft.parentCode}
                onChange={(event) => setPendingDraft((current) => ({ ...current, parentCode: event.target.value }))}
              />
              <TextField
                label="full_name"
                size="small"
                value={pendingDraft.fullName}
                onChange={(event) => setPendingDraft((current) => ({ ...current, fullName: event.target.value }))}
              />
            </>
          )}
          <TextField
            label="admin_comment"
            size="small"
            multiline
            minRows={3}
            value={pendingDraft.adminComment}
            onChange={(event) => setPendingDraft((current) => ({ ...current, adminComment: event.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPendingAction(null)}>Отмена</Button>
          <Button
            variant="contained"
            color={pendingAction?.mode === 'accept' ? 'primary' : 'error'}
            onClick={() => void handlePendingAction()}
            startIcon={pendingAction?.mode === 'accept' ? <CheckCircle2 size={15} /> : <X size={15} />}
          >
            {pendingAction?.mode === 'accept' ? 'Принять' : 'Отклонить'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

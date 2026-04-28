import React, { useState } from 'react';
import { 
  Dialog, 
  DialogContent, 
  Box, 
  Typography, 
  IconButton, 
  Button, 
  MobileStepper,
  Paper,
  Stack
} from '@mui/material';
import { X, ChevronRight, ChevronLeft, CheckCircle } from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { motion, AnimatePresence } from 'motion/react';

const SCENES = [
  {
    title: 'Чат инженера',
    description: 'Задавайте вопросы на естественном языке. Система найдет ответы в базе ГОСТов, чертежей и спецификаций, предоставив точные цитаты.',
    image: 'https://images.unsplash.com/photo-1531297484001-80022131f5a1?q=80&w=800&auto=format&fit=crop',
  },
  {
    title: 'Поиск и исследование',
    description: 'Профессиональный поиск по фрагментам текстов. Фильтруйте результаты по версии документа, типу и релевантности.',
    image: 'https://images.unsplash.com/photo-1454165833767-027521e4129b?q=80&w=800&auto=format&fit=crop',
  },
  {
    title: 'Реестр документов',
    description: 'Контролируйте статус обработки ваших документов. Система автоматически производит OCR и индексацию новых файлов.',
    image: 'https://images.unsplash.com/photo-1568667256549-094345857637?q=80&w=800&auto=format&fit=crop',
  },
  {
    title: 'Сверка параметров',
    description: 'Автоматическое выявление расхождений между разными версиями документов или чертежей для минимизации ошибок.',
    image: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=800&auto=format&fit=crop',
  },
  {
    title: 'Мониторинг качества',
    description: 'Отслеживайте метрики точности ответов и качество распознавания текста в реальном времени.',
    image: 'https://images.unsplash.com/photo-1551288049-bbbda536339a?q=80&w=800&auto=format&fit=crop',
  },
];

export const VideoGuideDialog: React.FC = () => {
  const { videoGuideOpen, setVideoGuideOpen } = useUIStore();
  const [activeStep, setActiveStep] = useState(0);

  const handleNext = () => setActiveStep((prev) => prev + 1);
  const handleBack = () => setActiveStep((prev) => prev - 1);

  return (
    <Dialog 
      fullScreen 
      open={videoGuideOpen} 
      onClose={() => setVideoGuideOpen(false)}
      slotProps={{
        paper: {
          sx: {
            bgcolor: 'background.default',
            background:
              'radial-gradient(circle at 22% 0%, rgba(112,161,255,0.12), transparent 30%), linear-gradient(135deg, #0b0c0e 0%, #11131a 48%, #0b0c0e 100%)',
          }
        }
      }}
    >
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <IconButton onClick={() => setVideoGuideOpen(false)} sx={{ color: 'text.secondary' }}>
          <X size={24} />
        </IconButton>
      </Box>

      <DialogContent
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          p: 4,
          pt: 2,
        }}
      >
        <Box
          sx={{
            maxWidth: 920,
            width: '100%',
            px: { xs: 2.5, md: 4.5 },
            py: { xs: 3, md: 4 },
            borderRadius: 4,
            border: '1px solid rgba(255,255,255,0.10)',
            bgcolor: 'rgba(22, 23, 27, 0.82)',
            boxShadow: '0 24px 60px rgba(0,0,0,0.32)',
            backdropFilter: 'blur(16px)',
          }}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={activeStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 4, alignItems: 'center' }}>
                <Box>
                  <Typography variant="overline" color="primary" sx={{ fontWeight: 700, letterSpacing: 2 }}>
                    Обучающая презентация
                  </Typography>
                  <Typography variant="h3" sx={{ mt: 1, mb: 3, fontWeight: 700 }}>
                    {SCENES[activeStep].title}
                  </Typography>
                  <Typography variant="h6" color="text.secondary" sx={{ mb: 4, lineHeight: 1.6, fontWeight: 400 }}>
                    {SCENES[activeStep].description}
                  </Typography>
                  
                  {activeStep === SCENES.length - 1 ? (
                    <Button 
                      variant="contained" 
                      size="large" 
                      onClick={() => setVideoGuideOpen(false)}
                      startIcon={<CheckCircle size={20} />}
                      sx={{ px: 4, py: 1.5, borderRadius: 2 }}
                    >
                      Понятно, приступить к работе
                    </Button>
                  ) : (
                    <Button 
                      variant="contained" 
                      size="large" 
                      onClick={handleNext}
                      endIcon={<ChevronRight size={20} />}
                      sx={{ px: 4, py: 1.5, borderRadius: 2 }}
                    >
                      Далее
                    </Button>
                  )}
                </Box>
                <Box>
                  <Paper 
                    elevation={24} 
                    sx={{ 
                      borderRadius: 4, 
                      overflow: 'hidden', 
                      aspectRatio: '4/3', 
                      position: 'relative',
                      border: '1px solid rgba(255,255,255,0.1)'
                    }}
                  >
                    <img 
                      src={SCENES[activeStep].image} 
                      alt={SCENES[activeStep].title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      referrerPolicy="no-referrer"
                    />
                    <Box 
                      sx={{ 
                        position: 'absolute', 
                        inset: 0, 
                        background: 'linear-gradient(to top, rgba(0,0,0,0.5), transparent)' 
                      }} 
                    />
                  </Paper>
                </Box>
              </Box>
            </motion.div>
          </AnimatePresence>

          <Box sx={{ mt: 8 }}>
            <MobileStepper
              variant="progress"
              steps={SCENES.length}
              position="static"
              activeStep={activeStep}
              sx={{ 
                bgcolor: 'transparent', 
                flexGrow: 1,
                '& .MuiLinearProgress-root': { 
                  width: '100%', 
                  height: 6, 
                  borderRadius: 3,
                  bgcolor: 'rgba(255,255,255,0.05)'
                }
              }}
              nextButton={
                <IconButton size="small" onClick={handleNext} disabled={activeStep === SCENES.length - 1} sx={{ ml: 2 }}>
                  <ChevronRight size={24} />
                </IconButton>
              }
              backButton={
                <IconButton size="small" onClick={handleBack} disabled={activeStep === 0} sx={{ mr: 2 }}>
                  <ChevronLeft size={24} />
                </IconButton>
              }
            />
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

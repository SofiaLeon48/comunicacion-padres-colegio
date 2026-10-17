// Dirección de la API. Se define en el archivo .env (VITE_API_URL) o en Vercel.
export const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
export const NOMBRE_APP = 'Conecta Escolar';
export const NOMBRE_COLEGIO = 'Institución Educativa';

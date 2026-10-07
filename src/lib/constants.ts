// Correo corporativo: destino de todos los botones de contacto de la web.
export const correo_patrocinio = "hola@tarsupv.com";

// Botones de la seccion de patrocinadores (/partners).
export const enlace_ser_patrocinador = `mailto:${correo_patrocinio}?subject=${encodeURIComponent(
  "Quiero ser patrocinador de TARS Robotics UPV"
)}`;
// Dossier de patrocinio 2026-27 (public/docs/). Al cambiar de temporada, sube
// el PDF nuevo y actualiza la ruta.
export const enlace_dossier_patrocinio = "/docs/Dosier_TARS_Robotics_2026-27.pdf";

// ============================================================================
//  BAUTEIL-KONFIGURATION
//  Die Schlüssel sind EXAKT die Node-Namen aus deinem SolidWorks-glTF-Export.
//  Hier änderst du alle Texte, Beschreibungen und Specs — sonst nichts anfassen.
// ============================================================================

export const PARTS = {
  'Linse-1': {
    label: 'Fokussierlinse',
    material: 'glass', // Sonderfall: wird als transparentes Glas gerendert
    desc: 'Bündelt den einfallenden Laserstrahl auf die aktive Fläche der Photodiode und vergrößert so die effektive Empfangsapertur.',
    specs: { Funktion: 'Fokussierung', Material: 'Glas / PMMA' },
  },
  'Tubus-1': {
    label: 'Tubus',
    desc: 'Inneres Tubusrohr, das die Linse fasst und den definierten Abstand zwischen Linse und Photodiode (Brennweite) einstellt.',
    specs: { Funktion: 'Linsenhalter', Fertigung: 'FDM-Druck' },
  },
  'Röhre-1': {
    label: 'Gehäuseröhre',
    desc: 'Äußeres Gehäuse des Empfängers. Schirmt die Photodiode gegen Umgebungslicht ab und nimmt die inneren Komponenten auf.',
    specs: { Funktion: 'Gehäuse', Fertigung: 'FDM-Druck' },
  },
  'Kleiner Deckel-1': {
    label: 'Rückdeckel',
    desc: 'Rückseitiger Deckel des Gehäuses. Fixiert die Photodiode und verschließt die Röhre lichtdicht.',
    specs: { Funktion: 'Verschluss', Fertigung: 'FDM-Druck' },
  },
  'Diode-1': {
    label: 'Photodiode',
    desc: 'Wandelt einfallendes Licht in einen Photostrom um. Dieser wird anschließend vom Transimpedanzverstärker (TIA) in eine Spannung gewandelt.',
    specs: { Typ: 'BPW34 (PIN)', Nachlauf: 'TIA → Komparator' },
  },
  'Untersatz-1': {
    label: 'Untersatz',
    desc: 'Basis des Empfängers. Verbindet das Gehäuse mechanisch mit dem Schienenaufsatz und richtet die optische Achse aus.',
    specs: { Funktion: 'Basis', Fertigung: 'FDM-Druck' },
  },
  'Schiene aufsatz receiver richtig-1': {
    label: 'Schienenaufsatz',
    desc: 'Aufsatz zur Montage des Empfängers auf der optischen Schiene. Erlaubt Verschieben entlang der Strecke zur Distanzeinstellung.',
    specs: { Funktion: 'Schienenmontage', Fertigung: 'FDM-Druck' },
  },
}

// Sammel-Eintrag für alle Normteile (Schrauben/Muttern/Bolzen).
// Node-Namen, die mit einem dieser Präfixe beginnen, gelten als Verschraubung.
export const FASTENER_PREFIXES = ['hex screw', 'hex nut', 'hex bolt']

export const FASTENER_INFO = {
  label: 'Verschraubung',
  desc: 'Genormte Schrauben, Muttern und Bolzen (ISO/DIN) aus der SolidWorks-Toolbox, die die Baugruppe zusammenhalten.',
  specs: { Norm: 'ISO / DIN', Anzahl: '12 Teile' },
}

export function isFastener(name) {
  return FASTENER_PREFIXES.some((p) => name.toLowerCase().startsWith(p))
}

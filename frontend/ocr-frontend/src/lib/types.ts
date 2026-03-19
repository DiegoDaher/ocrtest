export interface OCRFields {
  full_text: string;
  name: string | null;
  address: string | null;
  curp: string | null;
  birth_date: string | null;
  validity: string | null;
}

export interface OCRResponse {
  fields: OCRFields;
  metadata: Record<string, unknown>;
}

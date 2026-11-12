export function maskAccountNumber(acc: string | null | undefined): string {
  if (!acc) return "XXXX----";
  const str = String(acc).trim();
  if (str.startsWith("XXXX")) return str;
  if (str.length <= 4) return "XXXX" + str;
  return "XXXX" + str.slice(-4);
}

export function maskPhone(phone: string | null | undefined): string {
  if (!phone) return "—";
  const digits = phone.replace(/\D/g, '');
  if (digits.length >= 10) {
    return `${digits.slice(0, 2)}XXX X${digits.slice(-4)}`;
  }
  return phone;
}


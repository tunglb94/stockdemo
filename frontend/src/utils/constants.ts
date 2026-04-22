export const VN30_SYMBOLS = [
  "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR",
  "HDB", "HPG", "MBB", "MSN", "MWG", "PLX", "POW", "SAB",
  "SHB", "SSB", "SSI", "STB", "TCB", "TPB", "VCB", "VHM",
  "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
];

export const ORDER_TYPES = [
  { value: "LO", label: "LO - Giới hạn" },
  { value: "MP", label: "MP - Thị trường" },
  { value: "ATO", label: "ATO - Khớp lệnh mở cửa" },
  { value: "ATC", label: "ATC - Khớp lệnh đóng cửa" },
];

export const TRADING_HOURS = {
  ATO_START: "09:00",
  ATO_END: "09:15",
  MORNING_START: "09:15",
  MORNING_END: "11:30",
  AFTERNOON_START: "13:00",
  AFTERNOON_END: "14:30",
  ATC_START: "14:30",
  ATC_END: "14:45",
};

export const STATUS_LABELS: Record<string, string> = {
  PENDING: "Chờ khớp",
  MATCHED: "Đã khớp",
  PARTIAL: "Khớp một phần",
  CANCELLED: "Đã hủy",
  REJECTED: "Bị từ chối",
};

export const STATUS_COLORS: Record<string, string> = {
  PENDING: "bg-yellow-500/20 text-yellow-400",
  MATCHED: "bg-green-500/20 text-green-400",
  PARTIAL: "bg-blue-500/20 text-blue-400",
  CANCELLED: "bg-gray-500/20 text-gray-400",
  REJECTED: "bg-red-500/20 text-red-400",
};

# 📊 Dashboard API Documentation

## Base URL
```
http://localhost:8000
```

---

## 🔌 WebSocket Endpoint

### `WS /api/v1/dashboard/ws`

**Kết nối WebSocket để nhận real-time updates khi Google Sheet thay đổi.**

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/dashboard/ws');
```

#### Messages từ Server

**1. Data Update (Khi Sheet thay đổi)**
```json
{
  "type": "data_update",
  "timestamp": "2026-02-04T10:30:00",
  "rows_count": 35,
  "cols_count": 104,
  "data": [[...], [...]],  // Raw 2D array từ sheet
  "parsed": [               // Array of employee objects (structured)
    {
      "code": "LIE",
      "name": "Nguyễn Thị Liên",
      "status": "LIVE",
      "by_type": {
        "customers": {
          "2024": [1, 1, 1, 1],
          "2025": [1, 4, 2, 1],
          "2026": [1, 0, 0, 0]
        },
        "revenue": {
          "2024": [3500000, 3500000, 3500000, 3500000, 5000000, 5000000, 2300000, 1600000, 1200000, 1200000, 1200000, 1200000],
          "2025": [3500000, 3500000, ...],
          "2026": []
        },
        "debt": {
          "2024": ["100%", "100%", "100%", ...],
          "2025": ["100%", "100%", "100%", "88%", ...],
          "2026": ["0%", "0%", ...]
        },
        "payments": {
          "2024": [11340000, 0, 0, 11340000, ...],
          "2025": [11340000, 0, 0, 11340000, ...]
        },
        "receivables": {
          "2024": [11340000, 11340000, 11340000, 11340000],
          "2025": [11340000, 12840000, 7360000, 9000000],
          "2026": [9000000, 0, 0, 0]
        }
      }
    }
  ]
}
```

**2. Pong (Response to ping)**
```json
{
  "type": "pong",
  "timestamp": "2026-02-04T10:30:00"
}
```

#### Messages từ Client
```javascript
// Keep-alive ping
ws.send('ping');
```

---

## 📡 REST Endpoints

### 1. GET `/api/v1/dashboard/parsed`

**Lấy dữ liệu parsed (structured) của tất cả nhân viên.**

#### Response
```json
{
  "type": "parsed",
  "count": 27,
  "items": [
    {
      "code": "LIE",
      "name": "Nguyễn Thị Liên",
      "status": "LIVE",
      "by_type": {
        "customers": {
          "2024": [1, 1, 1, 1],
          "2025": [1, 4, 2, 1],
          "2026": [1, 0, 0, 0]
        },
        "revenue": {
          "2024": [3500000, 3500000, 3500000, 3500000, 5000000, 5000000, 2300000, 1600000, 1200000, 1200000, 1200000, 1200000],
          "2025": [3500000, 3500000, 3500000, 3500000, 5000000, 5000000, ...],
          "2026": []
        },
        "debt": {
          "2024": ["100%", "100%", "100%", "100%", "100%", "100%", ...],
          "2025": ["100%", "100%", "100%", "88%", "100%", ...],
          "2026": ["0%", "0%", "0%", ...]
        },
        "payments": {
          "2024": [11340000, 0, 0, 11340000, 0, 0, 11340000, ...],
          "2025": [11340000, 0, 0, 11340000, 0, 0, ...]
        },
        "receivables": {
          "2024": [11340000, 11340000, 11340000, 11340000],
          "2025": [11340000, 12840000, 7360000, 9000000],
          "2026": [9000000, 0, 0, 0]
        }
      }
    }
  ]
}
```

---

### 2. GET `/api/v1/dashboard/data`

**Lấy raw data từ Google Sheet (10 dòng đầu).**

#### Response
```json
{
  "type": "data",
  "timestamp": "2026-02-04T10:30:00",
  "rows_count": 35,
  "cols_count": 104,
  "data": [
    ["Header1", "Header2", ...],
    ["Row1Col1", "Row1Col2", ...],
    ...
  ],
  "message": "Sử dụng /dashboard/ws để kết nối WebSocket và nhận updates real-time"
}
```

---

### 3. GET `/api/v1/dashboard/health`

**Health check endpoint.**

#### Response
```json
{
  "status": "ok",
  "connected_clients": 2,
  "sheet_id": "1KF68El6c5-_2QwybKa2k-3N149L-xYU2-h6SsSAUXno"
}
```

---

## 📊 Data Structure (Employee Object)

Mỗi nhân viên trong `parsed.items[]` có cấu trúc:

```typescript
interface Employee {
  code: string;                    // Mã nhân viên (VD: "LIE")
  name: string;                    // Tên nhân viên
  status: string;                  // "LIVE" | "INACTIVE"
  
  customers: number[];             // 12 quý số lượng khách hàng (2024-2026)
  revenue_kpi: number[];           // 12 tháng doanh thu KPI
  
  by_year: {                       // ⭐ SỬ DỤNG ĐỂ VẼ BIỂU ĐỒ
    "2024": {
      customers_quarterly: number[];   // 4 quý [Q1, Q2, Q3, Q4]
      revenue_quarterly: number[];     // 4 quý (tổng từ revenue_kpi tháng)
      debt_kpi: string[];              // 12 tháng (VD: ["100%", "100%", ...])
      payment_monthly: number[];       // 12 tháng thanh toán
      receivables_quarterly: number[]; // 4 quý công nợ phải thu
    },
    "2025": {
      customers_quarterly: number[];   // 4 quý
      debt_kpi: string[];
      payment_monthly: number[];
      receivables_quarterly: number[];
    },
    "2026": {
      customers_quarterly: number[];   // 4 quý
      debt_kpi: string[];
      receivables_quarterly: number[]; // Chỉ có receivables (chưa có payment)
    }
  },
  
  // Legacy fields (tương thích ngược)
  debt_kpi_2024: string[];
  debt_kpi_2025: string[];
  debt_kpi_2026: string[];
  receivables_quarterly: number[];    // Tất cả 12 quý (2024-2026)
  payment_2024_monthly: number[];
  payment_2025_monthly: number[];
}
```

**Cấu trúc:** `type → year → quarters/months`

---

## 🎨 Frontend Implementation Examples

### 1. Connect WebSocket và Auto-update
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/dashboard/ws');

ws.onopen = () => {
  console.log('✅ Connected to Dashboard');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'data_update' && data.parsed) {
    console.log(`📊 Received ${data.parsed.length} employees`);
    renderDashboard(data.parsed);  // Update UI
  }
};

// Keep-alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);
```

### 2. Fetch Initial Data (REST)
```javascript
async function loadDashboard() {
  const response = await fetch('http://localhost:8000/api/v1/dashboard/parsed');
  const data = await response.json();
  
  if (data.items) {
    console.log(`Loaded ${data.count} employees`);
    renderDashboard(data.items);
  }
}
```

### 3. Vẽ Biểu Đồ theo Năm
```javascript
function renderCharts(employee) {
  // Biểu đồ khách hàng theo quý (2024-2026)
  const customersChart = {
    labels: ['Q1', 'Q2', 'Q3', 'Q4'],
    datasets: [
      {
        label: 'Khách hàng 2024',
        data: employee.by_type.customers['2024']
      },
      {
        label: 'Khách hàng 2025',
        data: employee.by_type.customers['2025']
      },
      {
        label: 'Khách hàng 2026',
        data: employee.by_type.customers['2026']
      }
    ]
  };
  
  // Biểu đồ doanh thu theo tháng (2024)
  const revenueChart = {
    labels: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12'],
    datasets: [
      {
        label: 'Doanh thu 2024',
        data: employee.by_type.revenue['2024']
      },
      {
        label: 'Doanh thu 2025',
        data: employee.by_type.revenue['2025']
      }
    ]
  };
  
  // Biểu đồ thanh toán hàng tháng
  const paymentChart = {
    labels: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12'],
    datasets: [
      {
        label: 'Thanh toán 2024',
        data: employee.by_type.payments['2024']
      },
      {
        label: 'Thanh toán 2025',
        data: employee.by_type.payments['2025']
      }
    ]
  };
  
  // Biểu đồ công nợ theo quý
  const receivablesChart = {
    labels: ['Q1', 'Q2', 'Q3', 'Q4'],
    datasets: [
      {
        label: 'Công nợ 2024',
        data: employee.by_type.receivables['2024']
      },
      {
        label: 'Công nợ 2025',
        data: employee.by_type.receivables['2025']
      },
      {
        label: 'Công nợ 2026',
        data: employee.by_type.receivables['2026']
      }
    ]
  };
  
  // Sử dụng Chart.js, Recharts, hoặc library khác
  createChart('canvas-customers', customersChart);
  createChart('canvas-revenue', revenueChart);
  createChart('canvas-payment', paymentChart);
  createChart('canvas-receivables', receivablesChart);
}
```

### 4. Filter và Group Data
```javascript
// Lọc nhân viên LIVE
const activeEmployees = employees.filter(emp => emp.status === 'LIVE');

// Tính tổng doanh thu 2024
const totalRevenue2024 = employees.reduce((sum, emp) => {
  return sum + emp.by_type.revenue['2024'].reduce((a, b) => a + b, 0);
}, 0);

// Tính tổng thanh toán 2024
const totalPayment2024 = employees.reduce((sum, emp) => {
  return sum + emp.by_type.payments['2024'].reduce((a, b) => a + b, 0);
}, 0);

// Lấy top performers theo doanh thu
const topPerformers = employees
  .map(emp => ({
    name: emp.name,
    revenue2024: emp.by_type.revenue['2024'].reduce((a, b) => a + b, 0),
    revenue2025: emp.by_type.revenue['2025'].reduce((a, b) => a + b, 0),
    customers2024: emp.by_type.customers['2024'].reduce((a, b) => a + b, 0)
  }))
  .sort((a, b) => b.revenue2024 - a.revenue2024)
  .slice(0, 10);
```

---

## 🔄 Update Frequency

- **WebSocket**: Real-time updates khi Google Sheet thay đổi
- **Polling interval**: 30 giây (có thể config trong `SHEET_POLLING_INTERVAL`)
- **REST API**: On-demand (gọi khi cần)

---

## 🛠️ Error Handling

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Fallback to REST API
  loadDashboard();
};

ws.onclose = () => {
  console.log('Disconnected, reconnecting...');
  setTimeout(() => connectWebSocket(), 3000);
};
```

---

## 📝 Column Mapping (Google Sheet)

| Metric | Columns | Description | Format |
|--------|---------|-------------|--------|
| **Employee Code** | B | Mã nhân viên | String |
| **Employee Name** | C | Tên nhân viên | String |
| **Employee Status** | D | Trạng thái (LIVE/INACTIVE) | String |
| **Customers (Khách hàng)** | F:Q | Số lượng khách hàng theo quý (12 quý, 2024-2026) | Number (4 quý/năm) |
| **Revenue KPI** | S:AD | Doanh thu KPI theo tháng (12 tháng, 2024-2026) | Number (12 tháng/năm) |
| **Debt KPI 2024** | AF:AQ | KPI công nợ 2024 (12 tháng) | String (%) |
| **Debt KPI 2025** | AR:BC | KPI công nợ 2025 (12 tháng) | String (%) |
| **Debt KPI 2026** | BD:BO | KPI công nợ 2026 (12 tháng) | String (%) |
| **Receivables** | BQ:CB | Công nợ phải thu đầu quý (12 quý, 2024-2026) | Number (4 quý/năm) |
| **Payment 2024** | CD:CO | Thanh toán 2024 (12 tháng) | Number |
| **Payment 2025** | CP:DA | Thanh toán 2025 (12 tháng) | Number |

---

## 📝 Notes

1. **Sử dụng `by_type` object** để truy cập dữ liệu theo loại → năm → quý/tháng.
2. **Customers**: 12 quý (Q1-24 đến Q4-26), nhóm theo năm
   ```
   by_type.customers['2024'] = [Q1, Q2, Q3, Q4]
   by_type.customers['2025'] = [Q1, Q2, Q3, Q4]
   by_type.customers['2026'] = [Q1, Q2, Q3, Q4]
   ```
3. **Revenue**: 12 tháng (T1-T12) mỗi năm, nhóm theo năm
   ```
   by_type.revenue['2024'] = [T1, T2, ..., T12]
   by_type.revenue['2025'] = [T1, T2, ..., T12]
   by_type.revenue['2026'] = [T1, T2, ..., T12]
   ```
4. **Debt**: 12 tháng mỗi năm, format là phần trăm (%)
   ```
   by_type.debt['2024'] = ["100%", "100%", ..., "100%"]
   by_type.debt['2025'] = ["100%", "100%", ..., "88%"]
   by_type.debt['2026'] = ["0%", "0%", ...]
   ```
5. **Receivables**: 12 quý (4 quý/năm), công nợ phải thu đầu quý
   ```
   by_type.receivables['2024'] = [Q1, Q2, Q3, Q4]
   by_type.receivables['2025'] = [Q1, Q2, Q3, Q4]
   by_type.receivables['2026'] = [Q1, Q2, Q3, Q4]
   ```
6. **Payments**: 12 tháng mỗi năm (chỉ có 2024 và 2025)
   ```
   by_type.payments['2024'] = [T1, T2, ..., T12]
   by_type.payments['2025'] = [T1, T2, ..., T12]
   ```
7. **WebSocket preferred** cho real-time updates; REST API dùng làm fallback.
8. **Keep-alive ping** cần thiết để giữ WebSocket connection active.

---

## 🚀 Quick Start Frontend

```html
<!DOCTYPE html>
<html>
<head>
  <title>Dashboard KPI</title>
</head>
<body>
  <div id="employees-list"></div>
  <div id="charts"></div>
  
  <script>
    const ws = new WebSocket('ws://localhost:8000/api/v1/dashboard/ws');
    
    ws.onopen = () => {
      console.log('✅ Connected to Dashboard');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'data_update' && data.parsed) {
        console.log(`📊 Updated ${data.parsed.length} employees`);
        renderDashboard(data.parsed);
      }
    };
    
    // Keep-alive
    setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000);
    
    function renderDashboard(employees) {
      let html = '';
      
      for (const emp of employees) {
        const rev2024 = emp.by_type.revenue['2024'].reduce((a, b) => a + b, 0).toLocaleString('vi-VN');
        const rev2025 = emp.by_type.revenue['2025'].reduce((a, b) => a + b, 0).toLocaleString('vi-VN');
        const pay2024 = emp.by_type.payments['2024'].reduce((a, b) => a + b, 0).toLocaleString('vi-VN');
        const cust2024 = emp.by_type.customers['2024'].reduce((a, b) => a + b, 0);
        
        html += `
          <div style="border: 1px solid #ccc; padding: 10px; margin: 5px;">
            <h3>${emp.code} - ${emp.name} (${emp.status})</h3>
            <table>
              <tr>
                <td><strong>Doanh thu 2024:</strong></td>
                <td>${rev2024} VND</td>
              </tr>
              <tr>
                <td><strong>Doanh thu 2025:</strong></td>
                <td>${rev2025} VND</td>
              </tr>
              <tr>
                <td><strong>Thanh toán 2024:</strong></td>
                <td>${pay2024} VND</td>
              </tr>
              <tr>
                <td><strong>Khách hàng 2024:</strong></td>
                <td>${cust2024} khách</td>
              </tr>
              <tr>
                <td><strong>Công nợ 2024:</strong></td>
                <td>${emp.by_type.receivables['2024'][3]} VND (Q4)</td>
              </tr>
            </table>
          </div>
        `;
      }
      
      document.getElementById('employees-list').innerHTML = html;
    }
  </script>
</body>
</html>
```

---

## 📋 Dữ liệu từ Google Sheet

Khi dữ liệu được fetch từ Google Sheet, nó sẽ được parse và tổ chức lại theo cấu trúc `by_type`:

```
Google Sheet columns:
  B (Code)    C (Name)           D (Status)
  F:Q         S:AD               AF:AQ         AR:BC         BD:BO         BQ:CB               CD:CO           CP:DA
  Customers   Revenue KPI        Debt 2024     Debt 2025     Debt 2026     Receivables         Payment 2024    Payment 2025
  (12 quý)    (12 tháng)        (12 tháng)    (12 tháng)    (12 tháng)    (12 quý)            (12 tháng)      (12 tháng)
         ↓
       Parser (dashboard_sheet_service.py)
         ↓
Cấu trúc JSON:
{
  "code": "LIE",
  "name": "Nguyễn Thị Liên",
  "status": "LIVE",
  "by_type": {
    "customers": {
      "2024": [Q1, Q2, Q3, Q4],       // từ F:I
      "2025": [Q1, Q2, Q3, Q4],       // từ J:M
      "2026": [Q1, Q2, Q3, Q4]        // từ N:Q
    },
    "revenue": {
      "2024": [T1, T2, ..., T12],     // từ S:AD (12 tháng)
      "2025": [T1, T2, ..., T12],
      "2026": [T1, T2, ..., T12]
    },
    "debt": {
      "2024": [T1%, T2%, ..., T12%],  // từ AF:AQ
      "2025": [T1%, T2%, ..., T12%],  // từ AR:BC
      "2026": [T1%, T2%, ..., T12%]   // từ BD:BO
    },
    "payments": {
      "2024": [T1, T2, ..., T12],     // từ CD:CO
      "2025": [T1, T2, ..., T12]      // từ CP:DA
    },
    "receivables": {
      "2024": [Q1, Q2, Q3, Q4],       // từ BQ:BT
      "2025": [Q1, Q2, Q3, Q4],       // từ BU:BX
      "2026": [Q1, Q2, Q3, Q4]        // từ BY:CB
    }
  }
}
```

---

## 🚀 Quick Start Frontend

```html
<!DOCTYPE html>
<html>
<head>
  <title>Dashboard</title>
</head>
<body>
  <div id="employees"></div>
  
  <script>
    const ws = new WebSocket('ws://localhost:8000/api/v1/dashboard/ws');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'data_update' && data.parsed) {
        renderEmployees(data.parsed);
      }
    };
    
    function renderEmployees(employees) {
      const html = employees.map(emp => `
        <div>
          <h3>${emp.code} - ${emp.name} (${emp.status})</h3>
          <p>Doanh thu 2024: ${emp.by_year['2024'].payment_monthly.reduce((a,b) => a+b, 0).toLocaleString()} VND</p>
          <p>Doanh thu 2025: ${emp.by_year['2025'].payment_monthly.reduce((a,b) => a+b, 0).toLocaleString()} VND</p>
        </div>
      `).join('');
      
      document.getElementById('employees').innerHTML = html;
    }
  </script>
</body>
</html>
```

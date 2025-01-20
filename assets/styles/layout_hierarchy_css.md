dbc.Container (fluid=True)
│
├── Store Components (hidden)
│   ├── _hidden-init-trigger
│   ├── show-data-table
│   ├── processed-data-store
│   ├── filter-state-store
│   ├── insurance-lines-state
│   ├── expansion-state
│   ├── tree-state
│   └── period-type
│
├── Navbar (class: main-nav)
│
├── Hidden Components
│   ├── dummy-output
│   └── dummy-trigger
│
├── Tree Container (class: tree-container)
│
├── Lines Checklist Buttons
│
├── CardBody (class: layout-wrapper)
│   └── Row
│       ├── Left Column (md=6)
│       │   ├── Sidebar Toggle Button (class: btn-sidebar-toggle-show/hide)
│       │   ├── Filters
│       │   ├── Filters
│       │   │   ├── Filters Row (class: sidebar-col)
│       │   │   │   ├── Left Column (xs=12, md=6, class: main-filter-column)
│       │   │   │   │   └── First Row (class: filter-row-no-margin)
│       │   │   │   │       └── Insurance / Line Switch (class: checklist)
│       │   │   │   │
│       │   │   │   └── Right Column (xs=12, md=6, class: filter-column)
│       │   │   │       └── First Row (class: filter-row-no-margin)
│       │   │   │           └── Insurer (class: dd-control)
│       │   │   │
│       │   │   ├── Additional Filters Row (class: sidebar-col/sidebar-col collapsed, id: sidebar-col)
│       │   │   │   ├── Left Column (xs=12, md=6, class: filter-column)
│       │   │   │   │   ├── Reporting Form Row (class: filter-row-no-margin)
│       │   │   │   │   ├── End Quarter Row (class: filter-row-no-margin)
│       │   │   │   │   ├── Period Type Row (class: filter-row)
│       │   │   │   │   │   └── Period Type Text (class: period-type__text)
│       │   │   │   │   └── Premium Loss Row (class: filter-row-no-margin)
│       │   │   │   │
│       │   │   │   └── Right Column (xs=12, md=6, class: filter-column)
│       │   │   │       ├── Market Share Toggle Row (class: filter-row-no-margin)
│       │   │   │       ├── Dynamic Toggle Row (class: filter-row-no-margin)
│       │   │   │       ├── Periods Input Row (class: filter-row-no-margin)
│       │   │   │       ├── Insurers Input Row (class: filter-row-no-margin)
│       │   │   │       └── Secondary Metric Row (class: filter-row-no-margin)
│       │   │   │
│       │   │   └── Main Filters Row (class: sidebar-col)
│       │   │       ├── Left Column (xs=12, md=6, class: main-filter-column)
│       │   │       │   └── Insurance Line Row (class: filter-row-no-margin)
│       │   │       └── Right Column (xs=12, sm=12, md=6, class: main-filter-column)
│       │   │           └── Primary Metric Row (class: filter-row-no-margin)
│       │   │    
│       │   └── Table Section
│       │       ├── Titles (class: titles-container)
│       │       │   ├── Table Title (class: table-title)
│       │       │   └── Table Subtitle (class: table-subtitle)
│       │       └── Data Table (class: datatable-container)
│       │
│       └── Right Column (md=6)
│           └── Market Analysis (id: market-analysis-container)
│               ├── Title (class: market-analysis-title)
│               ├── Cards Row
│               │   ├── Market Volume Card (class: card-container)
│               │   ├── Market Concentration Card (class: card-container)
│               │   └── Leaders Card (class: card-container)
│               │
│               ├── Tabs (class: tabs-container)
│               │   ├── Overview Tab (class: tab/tab-selected)
│               │   ├── Changes Tab (class: tab/tab-selected)
│               │   ├── Growth Tab (class: tab/tab-selected)
│               │   └── Contribution Tab (class: tab/tab-selected)
│               └── Tab Content (class: market-analysis-content)
│
└── Chart Container (class: chart-container/chart-container collapsed)
    ├── Chart Titles (class: titles-container-chart)
    │   ├── Chart Title (class: table-title)
    │   └── Chart Subtitle (class: table-subtitle)
    └── Graph Container (class: graph-container)
        └── Graph (dcc.Graph, style: height=100%, width=100%)

Form Element Classes:
- Dropdowns: class: dd-control
- Checklists: class: checklist
- Inputs: class: form-control input-short
- Buttons: class: btn-custom variants (btn-period, btn-sidebar-toggle-show/hide, btn-tab, btn-table-tab)
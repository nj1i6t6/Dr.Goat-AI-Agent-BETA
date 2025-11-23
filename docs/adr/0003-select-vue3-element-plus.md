# ADR 0003: Select Vue 3 + Element Plus for the frontend UI

## Background
The project targets a responsive management console that shares components with existing Vue-based internal tools. The team has existing expertise in Vue 3 Composition API, and Element Plus offers production-ready components with Traditional Chinese localisation, aligning with the target audience.

## Decision
Build the SPA with Vue 3, Vite, and Element Plus as the primary component library. Use Pinia for state management and Axios for HTTP requests.

## Consequences
- **Positive**: Accelerates delivery through familiar tooling, ensures consistent design tokens, and integrates smoothly with our existing charting stack (ECharts/Chart.js).
- **Negative**: Couples the UI to Element Plus styling conventions, which may require custom overrides to meet future branding changes. New contributors must be comfortable with the Composition API paradigm.

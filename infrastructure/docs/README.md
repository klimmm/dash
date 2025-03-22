# Insurance Analytics Dashboard


## Overview

This application provides a powerful analytics platform for insurance data visualization and analysis. It allows users to explore metrics across different insurance lines, companies, and time periods, with capabilities for filtering, ranking, market share analysis, and period-over-period comparisons.

### Key Features

- **Multi-dimensional Analytics**: Analyze insurance data across multiple dimensions (companies, lines, time periods)
- **Advanced Metrics**: Calculate key insurance metrics including loss ratios, market share, and growth rates
- **Interactive Visualization**: Dynamic charts and tables that respond to user selections
- **Hierarchical Data Navigation**: Explore insurance lines through an intuitive tree structure
- **Flexible Time Period Analysis**: Support for YTD, YoY, QoQ, and MAT analysis
- **Top-N Analysis**: Focus on top performers in the market

## Getting Started

### Prerequisites

- Python 3.7+
- Pip package manager
- Git (for cloning the repository)

### Installation

1. Clone the repository
```bash
git clone https://github.com/your-organization/insurance-analytics-dashboard.git
cd insurance-analytics-dashboard
```

2. Create and activate a virtual environment (recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run the application
```bash
python main.py
```

The application will be available at http://localhost:8051 by default.

### Data Files

The application requires insurance data files in the following structure:

```
data/
  raw/
    3rd_158_net.csv  # Form 158 data
    3rd_162_net.csv  # Form 162 data
  json/
    hierarchy_insurence_lines_158.json  # Insurance lines hierarchy for Form 158
    hierarchy_insurence_lines_162.json  # Insurance lines hierarchy for Form 162
```

## Architecture

The application follows a domain-driven design with clear separation of concerns:

![Architecture Diagram](https://via.placeholder.com/800x400?text=Architecture+Diagram)

### Core Layers

- **Domain Layer**: Contains business logic and domain-specific rules
- **Application Layer**: Coordinates services and orchestrates data flow
- **Presentation Layer**: Handles UI components and layouts 
- **Shared Layer**: Provides cross-cutting concerns and utilities

### Technology Stack

- **Dash/Plotly**: For interactive web interface and visualization
- **Pandas**: For data manipulation and analysis
- **Flask**: Underlying web framework for Dash
- **Bootstrap**: UI component styling

## Usage Guide

### Navigation

The application interface consists of several key sections:

1. **Top Navigation Bar**: Access to different views and global controls
2. **Sidebar**: Filtering options for data selection
3. **Main Content Area**: Visualizations and data tables
4. **Controls Panel**: Options for customizing the current view

### Data Selection

1. Select reporting form (0420158 or 0420162)
2. Choose insurance lines from the hierarchical tree
3. Select metrics of interest
4. Pick insurers for comparison or use the Top-N feature
5. Set the time period and analysis type

### Visualization Options

- **Table View**: Multi-dimensional analysis through pivoting
- **Chart View**: Visual representation of data with various chart types

### Analysis Types

- **YTD (Year-to-Date)**: Cumulative values from beginning of year to selected quarter
- **YoY-Q (Year-over-Year Quarterly)**: Same quarter comparison across years
- **YoY-Y (Year-over-Year Yearly)**: Annual comparison at same quarter
- **QoQ (Quarter-over-Quarter)**: Adjacent quarters comparison
- **MAT (Moving Annual Total)**: Rolling 12-month performance

## Development

### Project Structure

```
application/          # Application layer with coordination logic
  processing/         # Data processing services
  visualization/      # Visualization components
assets/               # Static assets
  styles/             # CSS styles
data/                 # Data files
domain/               # Domain layer with business logic
  components/         # Domain-specific UI components
  insurers/           # Insurance company logic
  lines/              # Insurance lines logic
  metrics/            # Metrics calculation and definition
  period/             # Time period handling
logger/               # Logging framework
presentation/         # UI components and layouts
shared/               # Cross-cutting concerns
```

### Adding New Features

### Testing

Run the tests with:

```bash
python -m pytest tests/
```

The project uses:
- Unit tests for domain logic
- Integration tests for data processing
- End-to-end tests for UI workflows

### Logging

The application uses a custom logging framework:

```python
from logger import logger

# Log at different levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

## Deployment

### Using Gunicorn (Recommended for Production)

```bash
gunicorn -c gunicorn_config.py wsgi:server
```

### Docker Deployment

### Environment Variables

The application can be configured with the following environment variables:

- `PORT`: Port number (default: 8051)
- `DEBUG`: Enable debug mode (default: True)

## Troubleshooting

### Common Issues

1. **Missing data files**: Ensure all required CSV and JSON files are present in the correct directories
2. **Performance issues**: For large datasets, increase the server resources or implement data pagination
3. **Visualization errors**: Check browser console for JavaScript errors and application logs for backend issues

### Debug Mode

Run the application in debug mode for additional information:

```bash
python main.py --debug
```

## Roadmap

### Upcoming Features

- Export capabilities for charts and data
- Additional visualization types (heatmaps, scatter plots)
- Advanced filtering options
- User-defined metrics
- Report generation and scheduling

### Known Limitations

- Performance may degrade with very large datasets (>1 million rows)
- Currently supports two reporting forms (0420158 and 0420162)
- Limited to quarterly data analysis

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows the project's coding standards and includes appropriate tests.

## Documentation

Comprehensive documentation is available in the [docs](docs/) directory:

- [Developer's Guide](docs/guides/developer-guide.md)
- [Architecture Overview](docs/architecture/architecture-decisions.md)
- [Domain Layer Documentation](docs/modules/domain/domain-layer.md)
- [Processing Module Documentation](docs/modules/application/processing.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Plotly/Dash](https://plotly.com/dash/) for the interactive visualization framework
- [Pandas](https://pandas.pydata.org/) for powerful data analysis capabilities
- All contributors who have helped shape this project

---

For questions or support, please open an issue on the GitHub repository.
// This file should be saved as 'clientside.js' in your app's 'assets' folder
// Dash automatically loads all .js files from the assets folder

if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.clientside = {
    // Detect viewport size and categorize based on custom breakpoints
    detectViewport: function(n_intervals) {
        var width = window.innerWidth;
        
        // Store the last detected viewport to avoid unnecessary updates
        if (!window.lastViewport) {
            window.lastViewport = '';
        }
        
        // Categorize viewport based on custom breakpoints
        var viewport;
        if (width < 390) {
            viewport = 'xs'; // Extra small
        } else if (width < 410) {
            viewport = 'sm'; // Small
        } else if (width < 530) {
            viewport = 'md'; // Medium
        } else if (width < 640) {
            viewport = 'lg'; // Large
        } else if (width < 768) {
            viewport = 'xl'; // Extra large
        } else if (width < 860) {
            viewport = 'xxl'; // Extra extra large
        } else if (width < 1024) {
            viewport = 'xxxl'; // Triple extra large
        } else {
            viewport = 'desktop'; // Desktop and above
        }
        
        // Only return a new value if the viewport category has changed
        if (viewport !== window.lastViewport) {
            console.log('Viewport changed to:', viewport, 'at width:', width);
            window.lastViewport = viewport;
            return viewport;
        }
        
        // Return no_update to avoid triggering callbacks when nothing changed
        return dash_clientside.no_update;
    },
    
    // Get the current root font size based on media queries
    getRootFontSize: function() {
        const rootFontSize = window.getComputedStyle(document.documentElement).fontSize;
        console.log('Current root font size:', rootFontSize);
        return parseFloat(rootFontSize);
    }
};

// Add a resize event listener for more immediate detection
window.addEventListener('resize', function() {
    // Throttle resize events to avoid excessive calculations
    if (this.resizeTimeout) {
        clearTimeout(this.resizeTimeout);
    }
    
    this.resizeTimeout = setTimeout(function() {
        var checkInterval = document.getElementById('viewport-check-interval');
        if (checkInterval) {
            // Trigger the interval to check viewport size
            checkInterval.setAttribute('n_intervals', 
                parseInt(checkInterval.getAttribute('n_intervals') || 0) + 1);
        }
    }, 250);
});

// Add a function to measure chart containers and font sizes
window.measureChartAndFonts = function() {
    const rootFontSize = parseFloat(window.getComputedStyle(document.documentElement).fontSize);
    console.log(`Root font size: ${rootFontSize}px`);
    
    const containers = document.querySelectorAll('.chart-wrapper');
    console.log(`Found ${containers.length} chart containers`);
    
    containers.forEach(function(container, index) {
        const rect = container.getBoundingClientRect();
        console.log(`Chart ${index + 1}: ${Math.round(rect.width)}px × ${Math.round(rect.height)}px`);
        
        // Find actual font sizes in the chart
        const chart = container.querySelector('.js-plotly-plot');
        if (chart) {
            const titleEl = chart.querySelector('.gtitle');
            const axisEl = chart.querySelector('.g-xtitle');
            const tickEl = chart.querySelector('.xtick text');
            
            if (titleEl) {
                const titleStyle = window.getComputedStyle(titleEl);
                console.log(`  Title font: ${titleStyle.fontSize} (${parseFloat(titleStyle.fontSize) / rootFontSize}rem)`);
            }
            
            if (axisEl) {
                const axisStyle = window.getComputedStyle(axisEl);
                console.log(`  Axis font: ${axisStyle.fontSize} (${parseFloat(axisStyle.fontSize) / rootFontSize}rem)`);
            }
            
            if (tickEl) {
                const tickStyle = window.getComputedStyle(tickEl);
                console.log(`  Tick font: ${tickStyle.fontSize} (${parseFloat(tickStyle.fontSize) / rootFontSize}rem)`);
            }
        }
    });
};

// Run the measurement after page load
document.addEventListener('DOMContentLoaded', function() {
    // Wait for charts to render
    setTimeout(window.measureChartAndFonts, 1000);
});
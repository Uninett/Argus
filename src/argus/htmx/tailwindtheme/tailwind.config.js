const projectPaths = [
    '../templates/**/*.html',
    './**/templates/**/*.html',
    'src/argus_htmx/templates/**/*.html',
    '!**/templates/**/admin/**'
];

const contentPaths = [...projectPaths];
console.log(`tailwindcss will scan ${contentPaths}`);

module.exports = {
    content: contentPaths,
    theme: {
        borderWidth: {
            DEFAULT: '2px',
            '0': '0',
            '1': '1px',
            '2': '2px',
            '3': '3px',
            '4': '4px',
            '6': '6px',
            '8': '8px',
        },
        ...{},
        extend:{
            colors: {
                "severity-primary-1": "red",
                "severity-primary-2": "orange",
                "severity-primary-3": "yellow",
                "severity-primary-4": "green",
                "severity-primary-5": "blue",
                "severity-secondary-1": "white",
                "severity-secondary-2": "black",
                "severity-secondary-3": "black",
                "severity-secondary-4": "white",
                "severity-secondary-5": "white",

            },
        },
    },
    safelist: [
        "htmx-request"
    ],
}

# Tailwind CSS Setup

This project uses Tailwind CSS for styling, configured via PostCSS.

## Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Watch for changes (development):**
   ```bash
   npm run watch-css
   ```
   This will automatically rebuild CSS when you make changes to templates or the input CSS file.

3. **Build for production:**
   ```bash
   npm run build-css
   ```
   This creates a minified CSS file in `static/landing/css/main.css`.

## Production Deployment

Before deploying to production, ensure you:

1. Run `npm run build-css` to generate the production CSS
2. Collect static files: `python manage.py collectstatic`
3. The compiled CSS will be included in your static files

## File Structure

- `static/landing/css/input.css` - Source CSS with Tailwind directives
- `static/landing/css/main.css` - Compiled CSS (generated, should be committed)
- `tailwind.config.js` - Tailwind configuration
- `postcss.config.js` - PostCSS configuration
- `package.json` - npm dependencies and scripts

## Custom Classes

The project includes custom utility classes defined in `input.css`:
- `.btn-primary`, `.btn-primary-large`
- `.btn-secondary`, `.btn-secondary-large`
- `.btn-white-large`, `.btn-outline-white`
- `.feature-card`, `.feature-icon`
- `.pricing-card`, `.pricing-badge`
- `.testimonial-card`
- And more...

These classes are available throughout the templates.

// head-content.js
document.addEventListener('DOMContentLoaded', function() {
    const headContent = `
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <link rel="icon" href="../frontend/assets/favicon.ico" type="image/x-icon">
        <link rel="shortcut icon" href="../frontend/assets/favicon.ico" type="image/x-icon">
        <link rel="icon" type="image/png" sizes="32x32" href="../frontend/assets/favicon-32x32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="../frontend/assets/favicon-16x16.png">
        <link rel="apple-touch-icon" sizes="180x180" href="../frontend/assets/apple-touch-icon.png">
        <link rel="apple-touch-icon" href="../frontend/assets/apple-touch-icon.png">
        <link rel="mask-icon" href="../frontend/assets/safari-pinned-tab.svg" color="#4f46e5">
        <link rel="manifest" href="../frontend/assets/site.webmanifest">

        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    `;
    
    // Insert before existing head content or at the end of head
    document.head.insertAdjacentHTML('beforeend', headContent);
});
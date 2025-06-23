/**
 * Custom Dashboard Redirect Script for Home Assistant
 * This script checks the current URL after login and redirects to 
 * the custom dashboard if on the default Lovelace URL.
 */
(function() {
  // Only run this script on the main page, not on the login page or other pages
  if (window.location.pathname === '/' || 
      window.location.pathname === '/lovelace' || 
      window.location.pathname.startsWith('/lovelace/')) {
    
    // Check if we have just logged in or loaded the default dashboard
    if (window.location.pathname === '/' || 
        window.location.pathname === '/lovelace' || 
        window.location.pathname === '/lovelace/0') {
      
      console.log("Redirecting to custom dashboard");
      
      // Small delay to ensure Home Assistant is fully loaded
      setTimeout(function() {
        window.location.assign('/custom-dashboard');
      }, 100);
    }
  }
})();

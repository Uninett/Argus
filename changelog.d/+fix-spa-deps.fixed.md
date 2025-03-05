Moved channels app from base settings to spa settings, where it belongs. The
dependency had already been moved, so this avoids an ImportError on new
installs. The spa frontend also needs CORS, but due to the complexity of when
the middleware needs to be called, the cors app and middleware have not been
moved, only the spa-specific setting.

(function($) {
	// ...existing code...

	// ...existing code...

	// ...existing code...
/*
	Future Imperfect by HTML5 UP
	html5up.net | @ajlkn
	Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)
*/

(function($) {

	var	$window = $(window),
		$body = $('body'),
		$menu = $('#menu'),
		$sidebar = $('#sidebar'),
		$main = $('#main');

	// Breakpoints.
		breakpoints({
			xlarge:   [ '1281px',  '1680px' ],
			large:    [ '981px',   '1280px' ],
			medium:   [ '737px',   '980px'  ],
			small:    [ '481px',   '736px'  ],
			xsmall:   [ null,      '480px'  ]
		});

	// Play initial animations on page load.
		$window.on('load', function() {
			window.setTimeout(function() {
				$body.removeClass('is-preload');
			}, 100);
		});

	// Menu.
		// Custom hamburger menu toggle
		$('#menuToggle').on('click', function(e) {
			e.preventDefault();
			$('#menu').toggleClass('visible');
		});
		// Hide menu when clicking outside or on a menu link
		$('#menu').on('click', function(e) {
			if ($(e.target).is('#menu') || $(e.target).is('a')) {
				$('#menu').removeClass('visible');
			}
		});

	// Intro.
		var $intro = $('#intro');

		// Move to main on <=large, back to sidebar on >large.
			breakpoints.on('<=large', function() {
				$intro.prependTo($main);
			});

			breakpoints.on('>large', function() {
				$intro.prependTo($sidebar);
			});

})(jQuery);
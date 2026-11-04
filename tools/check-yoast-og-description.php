<?php
/**
 * Braillewright - check: the theme's Yoast filter cuts only its own "Continue reading" tail.
 *
 * WHY THIS EXISTS
 * ---------------
 * braillewright_update_yoast_og_description() runs on Yoast SEO's wpseo_opengraph_desc filter. Yoast builds
 * the Open Graph description from the excerpt when a post has no description of its own, and the theme's
 * excerpt ends with its "Continue reading" link (the link text, then the post title for screen readers), so
 * the filter cuts that tail off. Up to 2.0.22 it did this with
 *
 *     substr( $ogdesc, 0, strpos( $ogdesc, $read_more_text ) )
 *
 * and strpos() returns false when the words are absent, which made the result an EMPTY string. Every post or
 * page with its own Yoast meta description therefore had no og:description and no oEmbed description at all,
 * so link previews on Facebook, LinkedIn, Mastodon and the rest showed none. Measured 2026-11-03: 451 of
 * 1,361 published posts and pages on toptechtidbits.com, 69 of 276 on accessinformationnews.com, 238 of 256
 * on drkirkadams.com, 139 of 146 on donnajodhan.com.
 *
 * WHAT IT CHECKS (exit 1 on any failure). Yoast does not need to be installed: the filter is called directly.
 *   1. A description the author wrote comes back unchanged.
 *   2. The excerpt-built description loses exactly the theme's tail, and nothing else.
 *   3. The real thing: the theme's own excerpt for a post, tags stripped as Yoast strips them, comes back
 *      without "Continue reading" and with all of its text before it.
 *   4. A chosen "read more" text is cut too, also when the theme printed it HTML-escaped (an ampersand).
 *   5. An empty description stays empty.
 *
 * Read-only: the post it uses is a copy held in memory, and every filter it adds is removed again.
 *
 * Run it with WP-CLI against any install running the theme:
 *     wp eval-file tools/check-yoast-og-description.php
 * CI runs it in the Accessibility job, inside wp-env, where .wp-env.json maps tools/ to
 * wp-content/braillewright-tools/.
 *
 * phpcs:disable WordPress.Security.EscapeOutput.OutputNotEscaped -- every echo below is
 * CLI diagnostic text written to a terminal, never rendered as HTML.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( ! function_exists( 'braillewright_update_yoast_og_description' ) ) {
	echo "FAIL: braillewright_update_yoast_og_description() is not defined. Is the theme active?\n";
	exit( 1 );
}

$braillewright_failures = 0;
$braillewright_total    = 0;

$braillewright_expect = function ( $label, $got, $want ) use ( &$braillewright_failures, &$braillewright_total ) {
	++$braillewright_total;
	if ( $got === $want ) {
		echo "ok    {$label}\n";
		return;
	}
	++$braillewright_failures;
	echo "FAIL  {$label}\n";
	echo '        expected: ' . wp_json_encode( $want, JSON_UNESCAPED_UNICODE ) . "\n";
	echo '        got:      ' . wp_json_encode( $got, JSON_UNESCAPED_UNICODE ) . "\n";
};

// 1. A description the author wrote.
$braillewright_own = 'Inside OneCourt, the company whose tactile broadcast lets blind fans feel the game.';
$braillewright_expect( "an author's own description comes back unchanged", braillewright_update_yoast_og_description( $braillewright_own ), $braillewright_own );

// 2. An excerpt-built description: the text, the theme's ellipsis, then its link text and the post title.
$braillewright_expect(
	'an excerpt-built description loses exactly the "Continue reading" tail',
	braillewright_update_yoast_og_description( 'The week&#8217;s news in access technology&#8230;Continue readingTop Tech Tidbits for Thursday' ),
	'The week&#8217;s news in access technology&#8230;'
);

// 3. The real thing: the theme's own excerpt of a post, stripped of tags the way Yoast strips it.
$braillewright_found = get_posts(
	array(
		'numberposts' => 1,
		'post_type'   => 'post',
		'post_status' => 'publish',
		'fields'      => 'ids',
	)
);
$braillewright_found = $braillewright_found ? get_post( (int) $braillewright_found[0] ) : null;
if ( ! $braillewright_found instanceof WP_Post ) {
	echo "FAIL: no published post to test with\n";
	exit( 1 );
}
$braillewright_post               = clone $braillewright_found;
$braillewright_post->post_excerpt = '';
$braillewright_saved              = isset( $GLOBALS['post'] ) ? $GLOBALS['post'] : null;
// phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited -- the loop sets the current post the same way.
$GLOBALS['post'] = $braillewright_post;
setup_postdata( $braillewright_post );
$braillewright_short = static function () {
	return 5;
};
add_filter( 'excerpt_length', $braillewright_short, 999 );
$braillewright_excerpt = wp_strip_all_tags( get_the_excerpt() );
remove_filter( 'excerpt_length', $braillewright_short, 999 );
wp_reset_postdata();
// phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited -- puts back the current post this check replaced.
$GLOBALS['post']       = $braillewright_saved;
$braillewright_link_at = strpos( $braillewright_excerpt, 'Continue reading' );
if ( false === $braillewright_link_at ) {
	++$braillewright_total;
	++$braillewright_failures;
	echo "FAIL  the theme's own excerpt carries no \"Continue reading\" to cut: {$braillewright_excerpt}\n";
} else {
	$braillewright_expect(
		"the theme's own excerpt, as Yoast sees it, keeps its text and loses its link",
		braillewright_update_yoast_og_description( $braillewright_excerpt ),
		substr( $braillewright_excerpt, 0, $braillewright_link_at )
	);
}

// 4. A chosen "read more" text, plain and with an ampersand (the theme prints it through esc_html()).
foreach ( array( 'Read the whole issue', 'Read more & see more' ) as $braillewright_text ) {
	$braillewright_mod = static function () use ( $braillewright_text ) {
		return $braillewright_text;
	};
	add_filter( 'theme_mod_read_more_text', $braillewright_mod );
	$braillewright_expect(
		"a chosen read-more text is cut too: {$braillewright_text}",
		braillewright_update_yoast_og_description( 'Issue text&#8230;' . esc_html( $braillewright_text ) . 'Issue 12' ),
		'Issue text&#8230;'
	);
	$braillewright_expect(
		"with a chosen read-more text, an author's own description is unchanged: {$braillewright_text}",
		braillewright_update_yoast_og_description( $braillewright_own ),
		$braillewright_own
	);
	remove_filter( 'theme_mod_read_more_text', $braillewright_mod );
}

// 5. Nothing in, nothing out.
$braillewright_expect( 'an empty description stays empty', braillewright_update_yoast_og_description( '' ), '' );

if ( $braillewright_failures ) {
	echo "\nFAILED: {$braillewright_failures} of {$braillewright_total} checks.\n";
	exit( 1 );
}

echo "\nPASSED: {$braillewright_total} of {$braillewright_total} checks.\n";

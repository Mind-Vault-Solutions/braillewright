<?php
/**
 * Braillewright - check: the "Continue reading" filter never reads a post that is not there.
 *
 * WHY THIS EXISTS
 * ---------------
 * braillewright_filter_read_more_link() in functions.php runs on the excerpt_more and
 * the_content_more_link filters, and it read the CURRENT post: $post->post_content.
 * WordPress also runs both filters for an excerpt or content built OUTSIDE the loop, where
 * there is no current post. Yoast SEO does exactly that on every oEmbed request
 * (/wp-json/oembed/1.0/embed, asked for by Mastodon, Facebook, Slack, Apple and WordPress
 * link previews): it answers with a description from get_the_excerpt( $post_id ), on a REST
 * request with no global $post, for every post without a meta description of its own.
 * Each one logged, up to 2.0.21:
 *
 *     PHP Warning:  Attempt to read property "post_content" on null
 *                   in .../themes/braillewright/functions.php on line 265
 *
 * toptechtidbits.com logged it 1,151 times in the 30 days to 2026-11-03. Of the 307 in the
 * last week, 303 came in the same second as an oEmbed request in the web server log.
 *
 * WHAT IT CHECKS (exit 1 on any failure)
 *   1. get_the_excerpt() of a post with no manual excerpt, with no current post (the oEmbed
 *      path), raises no PHP error, warning, notice or deprecation in a theme file.
 *   2. get_the_content() of a post with a more tag, with no current post: the same.
 *   3. Inside the loop nothing changed: the excerpt still carries the theme's "Continue
 *      reading" link to that post, with the post's title for screen readers.
 *
 * Read-only: every post it uses is a copy held in memory, and the current post is put back.
 *
 * Run it with WP-CLI against any install running the theme:
 *     wp eval-file tools/check-read-more-outside-loop.php
 * CI runs it in the Accessibility job, inside wp-env, where .wp-env.json maps tools/ to
 * wp-content/braillewright-tools/.
 *
 * phpcs:disable WordPress.Security.EscapeOutput.OutputNotEscaped -- every echo below is
 * CLI diagnostic text written to a terminal, never rendered as HTML.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

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

// A copy in memory with no manual excerpt, so WordPress builds the excerpt itself and runs
// excerpt_more, as it does for every older TTT newsletter. Nothing is saved.
$braillewright_post               = clone $braillewright_found;
$braillewright_post->post_excerpt = '';

$braillewright_more_post               = clone $braillewright_post;
$braillewright_more_post->post_content = "First part of the post.\n<!--more-->\nSecond part of the post.";

$braillewright_errors   = array();
$braillewright_failures = 0;
$braillewright_saved    = isset( $GLOBALS['post'] ) ? $GLOBALS['post'] : null;

// phpcs:ignore WordPress.PHP.DevelopmentFunctions.error_log_set_error_handler -- catching PHP errors raised in theme files is what this check is for.
set_error_handler(
	function ( $errno, $errstr, $errfile, $errline ) use ( &$braillewright_errors ) {
		if ( false !== strpos( wp_normalize_path( (string) $errfile ), '/themes/braillewright/' ) ) {
			$braillewright_errors[] = "PHP error {$errno}: {$errstr} in " . basename( (string) $errfile ) . ":{$errline}";
		}
		return false;
	}
);

$braillewright_report = function ( $label, $problems ) use ( &$braillewright_failures ) {
	if ( $problems ) {
		++$braillewright_failures;
		echo "FAIL  {$label}\n";
		foreach ( $problems as $braillewright_problem ) {
			echo "        {$braillewright_problem}\n";
		}
	} else {
		echo "ok    {$label}\n";
	}
};

// 1. The oEmbed path: an excerpt built with no current post.
// phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited -- a REST request has no current post; that is the case under test.
$GLOBALS['post']      = null;
$braillewright_errors = array();
$braillewright_text   = get_the_excerpt( $braillewright_post );
$braillewright_issues = $braillewright_errors;
if ( '' === trim( wp_strip_all_tags( $braillewright_text ) ) ) {
	$braillewright_issues[] = 'the excerpt came back empty';
}
$braillewright_report( 'excerpt with no current post (the oEmbed path): no PHP error in the theme', $braillewright_issues );

// 2. A more tag, with no current post.
$braillewright_errors = array();
get_the_content( null, false, $braillewright_more_post );
$braillewright_report( 'more tag with no current post: no PHP error in the theme', $braillewright_errors );

// 3. Inside the loop: the theme's link to the post, unchanged.
// phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited -- the loop sets the current post the same way.
$GLOBALS['post'] = $braillewright_post;
setup_postdata( $braillewright_post );
$braillewright_short = static function () {
	return 5;
};
add_filter( 'excerpt_length', $braillewright_short, 999 );
$braillewright_errors = array();
$braillewright_text   = get_the_excerpt();
remove_filter( 'excerpt_length', $braillewright_short, 999 );
$braillewright_issues = $braillewright_errors;
$braillewright_href   = 'href="' . esc_url( get_permalink( $braillewright_post ) ) . '"';
$braillewright_title  = '<span class="screen-reader-text">' . esc_html( get_the_title( $braillewright_post ) ) . '</span>';
if ( false === strpos( $braillewright_text, 'class="more-link"' ) ) {
	$braillewright_issues[] = 'no more-link in the excerpt: ' . $braillewright_text;
}
if ( false === strpos( $braillewright_text, $braillewright_href ) ) {
	$braillewright_issues[] = "the link does not point at the post ({$braillewright_href})";
}
if ( false === strpos( $braillewright_text, $braillewright_title ) ) {
	$braillewright_issues[] = "the post's title is not there for screen readers ({$braillewright_title})";
}
$braillewright_report( 'inside the loop: "Continue reading" links to the post, title for screen readers', $braillewright_issues );

wp_reset_postdata();
// phpcs:ignore WordPress.WP.GlobalVariablesOverride.Prohibited -- puts back the current post this check replaced.
$GLOBALS['post'] = $braillewright_saved;
restore_error_handler();

if ( $braillewright_failures ) {
	echo "\nFAILED: {$braillewright_failures} of 3 checks.\n";
	exit( 1 );
}

echo "\nPASSED: 3 of 3 checks.\n";

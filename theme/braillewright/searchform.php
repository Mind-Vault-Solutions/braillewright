<?php
// A page can print this form more than once (the 404 and search templates plus a
// Search widget), so the field id must be unique per form. aria_label comes from
// get_search_form( array( 'aria_label' => ... ) ), the same argument core's own form honors.
$braillewright_search_id    = wp_unique_id( 'search-field-' );
$braillewright_search_label = ! empty( $args['aria_label'] ) ? $args['aria_label'] : '';
?>
<div class='search-form-container'>
	<form role="search" method="get" class="search-form" action="<?php echo esc_url( home_url( '/' ) ); ?>"<?php echo $braillewright_search_label ? ' aria-label="' . esc_attr( $braillewright_search_label ) . '"' : ''; ?>>
		<label class="screen-reader-text" for="<?php echo esc_attr( $braillewright_search_id ); ?>"><?php esc_html_e( 'Search', 'braillewright' ); ?></label>
		<input id="<?php echo esc_attr( $braillewright_search_id ); ?>" type="search" class="search-field" value="" name="s"
				title="<?php esc_attr_e( 'Search for:', 'braillewright' ); ?>" placeholder="<?php esc_attr_e( 'Search for...', 'braillewright' ); ?>"/>
		<input type="submit" class="search-submit" value='<?php esc_attr_e( 'Search', 'braillewright' ); ?>'/>
	</form>
</div>

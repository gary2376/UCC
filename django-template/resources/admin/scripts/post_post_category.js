$(function () {
    let $post_category_selector = $('#id_post_category')
    let $sync_to_yahoo_news_selector = $('#id_sync_to_yahoo_news')

    function on_post_category_changed() {
        // let selected = $post_category_selector.val()
        let selected_text = $('#id_post_category option:selected').text()
        if (selected_text === 'M news') {
            $sync_to_yahoo_news_selector.closest('.form-row').show()
        } else {
            $sync_to_yahoo_news_selector.prop('checked', false);
            $sync_to_yahoo_news_selector.closest('.form-row').hide()
        }
    }

    $post_category_selector.change(function () {
        on_post_category_changed()
    })

    on_post_category_changed()
})

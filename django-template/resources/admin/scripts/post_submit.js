(function ($) {
    $(function () {
        $('#post_form').submit(function (e) {
            let check_input_ids = ['id_feature_media', 'id_thumbnail']
            let total_size_kb = 0
            $.each(check_input_ids, function (idx, check_input_id) {
                let val = $(`input#${check_input_id}`).val()
                if (val.indexOf('data:image/') >= 0) {
                    // https://stackoverflow.com/a/49750491
                    let string_length = val.length - 'data:image/png;base64,'.length;
                    let size_in_bytes = 4 * Math.ceil((string_length / 3)) * 0.5624896334383812;
                    let size_in_kb = size_in_bytes / 1024;
                    total_size_kb += size_in_kb
                }
            })
            console.log('total_size_kb: ' + total_size_kb)
            if (total_size_kb > 5 * 1024) {
                alert(`圖片容量為 ${total_size_kb} KB，已超過限制`)
                return false
            }
        })
    })
})(django.jQuery)

$(function () {
    let type_texts = {
        0: {
            label: '文字內容',
            help_text: '請直接填寫文字內容',
            rows: 10,
            resize: "both"
        },
        1: {
            label: '網址',
            help_text: '請填寫有效網址',
            rows: 1,
            resize: "none"
        },
        2: {
            label: '文章ID',
            help_text: '請填寫有效文章ID',
            rows: 1,
            resize: "none"
        }
    }

    let $type_selector = $('#id_type')

    function update_text() {
        let selected = $type_selector.val()
        if (!selected) {
            return
        }
        $('label[for=id_content]').text(type_texts[selected].label + ':')
        $('#id_content ~ .help').text(type_texts[selected].help_text)
        let $id_content_selector = $('#id_content')
        $id_content_selector[0].rows = type_texts[selected].rows
        $id_content_selector[0].style.resize = type_texts[selected].resize
    }

    $type_selector.change(function () {
        update_text()
    })

    update_text()
})

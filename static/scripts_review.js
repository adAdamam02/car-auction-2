document.addEventListener('DOMContentLoaded', function() {

    let max_selected = 7;

    let complete_purchase_span = document.getElementById('complete-purchase-span');

    let car_rows = document.getElementsByClassName('car-row');

    for (let i = 0; i < car_rows.length; i++)
    {
        let checkbox = car_rows[i].getElementsByClassName('car-selection-checkbox')[0];

        checkbox.addEventListener('click', function() {

            let n_checked_boxes = document.querySelectorAll('input[type="checkbox"]:checked').length;

            if (n_checked_boxes < max_selected)
            {
                complete_purchase_span.classList.add('d-none');
            }
            else
            {
                complete_purchase_span.classList.remove('d-none');
            }
        });
    }
});

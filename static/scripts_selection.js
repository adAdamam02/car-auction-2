// https://stackoverflow.com/questions/149055/how-to-format-numbers-as-currency-strings
let usd_formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0, // (causes 2500.99 to be printed as $2,501)
    });

document.addEventListener('DOMContentLoaded', function() {

    let car_rows = document.getElementsByClassName('car-row');
    
    let selected = parseInt(document.getElementById('selected-cars').innerHTML);
    let total = parseInt(document.getElementById('selected-total').innerHTML.replaceAll("$", "").replaceAll(",", ""));

    let max_selected = 7;
    let max_total = 100000;

    let overselection = false;
    let overspent = false;
    let underselection = true;

    let underselection_alert = document.getElementById('underselection');
    let overselection_alert = document.getElementById('overselection');
    let overspent_alert = document.getElementById('overspent');

    let review_selections_button = document.getElementById('review-selections-button');

    function check_submit_button() {
        underselection = (selected < max_selected) ? true : false;

        if (!underselection && !overselection && !overspent)
        {
            review_selections_button.classList.remove('btn-secondary');
            review_selections_button.classList.add('btn-primary');
        }
        else
        {
            review_selections_button.classList.remove('btn-primary');
            review_selections_button.classList.add('btn-secondary');
        }
    }

    check_submit_button();

    for (let i = 0; i < car_rows.length; i++)
    {
        let checkbox = car_rows[i].getElementsByClassName('car-selection-checkbox')[0];

        let car_price = car_rows[i].getElementsByClassName("car-price")[0].innerHTML;
        car_price = parseInt(car_price.replaceAll("$", "").replaceAll(",", ""));

        checkbox.addEventListener('click', function() {

            if (checkbox.checked)
            {
                selected += 1;
                total += car_price;
            }
            else
            {
                selected -= 1;                            
                total -= car_price;
            }

            if (selected > max_selected)
            {
                overselection_alert.innerHTML = `You selected ${selected} cars but you can only select ${max_selected} cars.`;
                overselection_alert.classList.remove('d-none');
                var remaining_cars_message = '0&nbsp&nbsp&nbsp&nbsp';
                overselection = true;
            }
            else
            {
                overselection_alert.classList.add('d-none');
                var remaining_cars_message = `${max_selected - selected}&nbsp&nbsp&nbsp&nbsp`;
                overselection = false;
            }

            if (total > max_total)
            {
                overspent_alert.innerHTML = `You spent ${usd_formatter.format(total)} but you can only spend ${usd_formatter.format(max_total)}.`;
                overspent_alert.classList.remove('d-none');
                var remaining_total_message = '$0';
                overspent = true;
            }
            else
            {
                overspent_alert.classList.add('d-none')
                var remaining_total_message = usd_formatter.format(max_total - total);
                overspent = false;
            }

            document.getElementById('selected-cars').innerHTML = `${selected}&nbsp&nbsp&nbsp&nbsp`;
            document.getElementById('remaining-cars').innerHTML = remaining_cars_message;

            document.getElementById('selected-total').innerHTML = usd_formatter.format(total);
            document.getElementById('remaining-total').innerHTML = remaining_total_message;

            underselection_alert.classList.add('d-none');

            check_submit_button();
        });
    }

    document.getElementById('car-selections-form').addEventListener('submit', function(event) {

        if (selected < max_selected)
        {   
            underselection_alert.innerHTML = `You selected ${selected} cars but you need to select ${max_selected} cars.`;
            underselection_alert.classList.remove('d-none');
            event.preventDefault();
        }
        else
        {
            if (overselection || overspent)
            {
                event.preventDefault();
            }
        }
    });
});

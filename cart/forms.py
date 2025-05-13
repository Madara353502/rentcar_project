from django import forms


PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 11)]


class CartAddProductForm(forms.Form):
    quantity = forms.TypedChoiceField(
        choices=PRODUCT_QUANTITY_CHOICES,
        coerce=int
    )
    override = forms.BooleanField(required=False,
                                  initial=False,
                                  widget=forms.HiddenInput)
    

class CartUpdateProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99,
                                widget=forms.NumberInput(attrs={'class': 'cart-quantity-input'}))
    override = forms.BooleanField(required=False,
                                  initial=False,
                                  widget=forms.HiddenInput)
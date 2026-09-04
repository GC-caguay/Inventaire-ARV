function arvToggleHolderMode() {
  var checked = document.querySelector('input[name="holder_mode"]:checked');
  var fields = document.getElementById('holder-fields');
  if (!checked || !fields) return;
  if (checked.value === 'other') {
    fields.classList.remove('hidden');
  } else {
    fields.classList.add('hidden');
    var memberSel = document.getElementById('holder_member_select');
    var partySel = document.getElementById('holder_party_select');
    var newParty = document.getElementById('new_party_name');
    if (memberSel) memberSel.value = '';
    if (partySel) partySel.value = '';
    if (newParty) newParty.value = '';
  }
}

function arvToggleSerialized(isSerialized) {
  var s = document.getElementById('serialized-fields');
  var f = document.getElementById('fungible-fields');
  if (!s || !f) return;
  if (isSerialized) {
    s.classList.remove('hidden');
    f.classList.add('hidden');
  } else {
    s.classList.add('hidden');
    f.classList.remove('hidden');
  }
}

var arvLineSeq = 0;

function arvInitCheckoutForm() {
  var picker = document.getElementById('item-picker');
  if (!picker || !window.ARV_ITEM_TYPES) return;
  Object.keys(window.ARV_ITEM_TYPES).forEach(function (id) {
    var it = window.ARV_ITEM_TYPES[id];
    var opt = document.createElement('option');
    opt.value = id;
    var suffix = it.is_serialized
      ? ' (' + it.units.length + ' en stock)'
      : ' (' + it.available_qty + ' ' + it.unit_label + ' dispo)';
    opt.textContent = it.name + suffix;
    picker.appendChild(opt);
  });
}

function arvAddLine() {
  var picker = document.getElementById('item-picker');
  var itemTypeId = picker.value;
  if (!itemTypeId) return;
  var it = window.ARV_ITEM_TYPES[itemTypeId];
  if (!it) return;

  arvAddLineRow(it, false, 1);

  (it.kit || []).forEach(function (kc) {
    var accessory = window.ARV_ITEM_TYPES[kc.item_type_id];
    if (!accessory) return;
    arvAddLineRow(accessory, true, kc.default_quantity);
  });

  picker.value = '';
}

function arvAddLineRow(it, isFromKit, defaultQty) {
  var container = document.getElementById('lines-container');
  var noLinesMsg = document.getElementById('no-lines-msg');
  if (noLinesMsg) noLinesMsg.classList.add('hidden');

  var row = document.createElement('div');
  row.className = 'kit-line' + (isFromKit ? ' from-kit' : '');

  var typeIdInput = document.createElement('input');
  typeIdInput.type = 'hidden';
  typeIdInput.name = 'line_item_type_id';
  typeIdInput.value = it.id;
  row.appendChild(typeIdInput);

  var fromKitInput = document.createElement('input');
  fromKitInput.type = 'hidden';
  fromKitInput.name = 'line_is_from_kit';
  fromKitInput.value = isFromKit ? '1' : '0';
  row.appendChild(fromKitInput);

  var nameSpan = document.createElement('span');
  nameSpan.className = 'name';
  nameSpan.textContent = it.name + (isFromKit ? ' (inclus par défaut)' : '');
  row.appendChild(nameSpan);

  if (it.is_serialized) {
    var unitSelect = document.createElement('select');
    unitSelect.name = 'line_item_unit_id';
    unitSelect.className = 'qty-input';
    if (!it.units || it.units.length === 0) {
      var emptyOpt = document.createElement('option');
      emptyOpt.value = '';
      emptyOpt.textContent = 'Aucune unité dispo';
      unitSelect.appendChild(emptyOpt);
      unitSelect.disabled = true;
    } else {
      it.units.forEach(function (u) {
        var opt = document.createElement('option');
        opt.value = u.id;
        opt.textContent = u.label;
        unitSelect.appendChild(opt);
      });
    }
    row.appendChild(unitSelect);

    var qtyHidden = document.createElement('input');
    qtyHidden.type = 'hidden';
    qtyHidden.name = 'line_quantity';
    qtyHidden.value = '1';
    row.appendChild(qtyHidden);
  } else {
    var unitHidden = document.createElement('input');
    unitHidden.type = 'hidden';
    unitHidden.name = 'line_item_unit_id';
    unitHidden.value = '';
    row.appendChild(unitHidden);

    var qtyInput = document.createElement('input');
    qtyInput.type = 'number';
    qtyInput.name = 'line_quantity';
    qtyInput.className = 'qty-input';
    qtyInput.min = '1';
    qtyInput.max = String(it.available_qty);
    qtyInput.value = String(defaultQty || 1);
    row.appendChild(qtyInput);

    var maxLabel = document.createElement('span');
    maxLabel.className = 'muted';
    maxLabel.style.fontSize = '0.8rem';
    maxLabel.textContent = '/ ' + it.available_qty + ' dispo';
    row.appendChild(maxLabel);
  }

  var removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn small secondary';
  removeBtn.textContent = 'Retirer';
  removeBtn.onclick = function () {
    row.remove();
    var c = document.getElementById('lines-container');
    var msg = document.getElementById('no-lines-msg');
    if (msg && c.children.length === 0) msg.classList.remove('hidden');
  };
  row.appendChild(removeBtn);

  container.appendChild(row);
}

// datos.js define: var HOY='05/11/26'; var CARTELES=[{nombre,precio,ean,cod,rubro},...]
var MARCAS=[['LA SERE.','La Serenísima'],['LA SERE','La Serenísima'],['LA SERENISIMA','La Serenísima'],['DON SATUR','Don Satur'],['3 ARROYOS','3 Arroyos'],['COCA COLA','Coca-Cola'],['VILLA DEL SUR','Villa del Sur'],['LA CAMPAGNOLA','La Campagnola'],['LA VIRGINIA','La Virginia'],['SAN IGNACIO','San Ignacio'],['ALTA MODA','Alta Moda'],['LA PAULINA','La Paulina'],['DOÑA PAULA','Doña Paula'],['EL TIO','El Tío'],['LA HOLANDO','La Holando'],['LA MORENITA','La Morenita'],['SANTA ANA','Santa Ana'],['DOS ANCLAS','Dos Anclas'],['LA PARMESANA','La Parmesana'],['VIEJO ALMACEN','Viejo Almacén'],['DON VICENTE','Don Vicente'],['LA SALTEÑA','La Salteña'],['PAPEL ELEGANTE','Papel Elegante']];
var SIN_MARCA=/verduler|fruta|carnic|fiambr|panader/i;
function fmt(n){return Math.round(n).toLocaleString('es-AR');}
function tc(w){return w.charAt(0).toUpperCase()+w.slice(1).toLowerCase();}
function armar(x){
  var s=(x.nombre||'').trim().replace(/\s+/g,' '), u=s.toUpperCase(), m=null, p=x.precio;
  for(var i=0;i<MARCAS.length;i++){var k=MARCAS[i][0]; if(u.indexOf(k+' ')===0){m=MARCAS[i][1]; s=s.slice(k.length).trim(); break;}}
  if(m===null){ if(SIN_MARCA.test(x.rubro||'')) m=''; else { var w=s.split(' ')[0]; m=tc(w); s=s.slice(w.length).trim(); } }
  var U=s.toUpperCase(), kg='';
  if(/(EL KILO|X ?KILO|X ?KGS?\.?$)/.test(U)) kg='Precio por kg <b>$'+fmt(p)+'</b>';
  else { var r=/X?\s*(\d+(?:[.,]\d+)?)\s*(KGR?S?\.?|KILO|GRS?\.?|GR\.?|ML|CM3?|CC|LTR?S?\.?|LT\.?|K|L)(?![A-Z])/.exec(U);
    if(r){var q=parseFloat(r[1].replace(',','.')),un=r[2],g; if(un[0]=='K') g=q<50?q*1000:q; else if(un[0]=='L') g=q*1000; else g=q;
      var lab=(un[0]=='K'||un[0]=='G')?'kg':'litro'; if(g>0) kg='Precio por '+lab+' <b>$'+fmt(p*1000/g)+'</b>';}}
  var n=s.charAt(0).toUpperCase()+s.slice(1).toLowerCase(); n=n.replace(/\bx\s*(\d)/g,'x $1');
  return {m:m,n:n,p:p,kg:kg||'&nbsp;',ean:x.ean,cod:x.cod};
}
function cartel(x){
  var top=[x.m,(!x.ean&&x.cod)?'Cód. '+x.cod:(x.cod?'Int. '+x.cod:'')].filter(Boolean).join(' · ');
  return '<div class="c"><div class="in"><span class="marca">'+top+'</span><span class="nom">'+x.n+'</span>'+
   '<span class="precio"><small>$</small>'+fmt(x.p)+'</span><div class="pie">'+(x.ean?'<svg data-ean="'+x.ean+'"></svg>':'<span></span>')+
   '<span class="t">'+x.kg+'<br>Impreso '+HOY+'</span></div></div></div>';
}
var D=CARTELES.map(armar), h='';
for(var i=0;i<D.length;i+=24){h+='<div class="sheet t1"><div class="grid">';
  D.slice(i,i+24).forEach(function(x){h+=cartel(x);}); h+='</div></div>';}
document.getElementById('hojas').innerHTML=h;
document.querySelectorAll('svg[data-ean]').forEach(function(el){
  try{JsBarcode(el,el.dataset.ean,{format:'CODE128',displayValue:true,fontSize:18,height:56,margin:0,background:'transparent',lineColor:'#111'});}catch(e){el.remove();}
});

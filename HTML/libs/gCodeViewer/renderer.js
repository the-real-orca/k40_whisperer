/**
 * User: hudbrog (hudbrog@gmail.com)
 * Date: 10/20/12
 * Time: 1:36 PM
 * To change this template use File | Settings | File Templates.
 */


GCODE.renderer = (function(){
// ***** PRIVATE ******
    var canvas;
    var ctx;
    var zoomFactor= 3, zoomFactorDelta = 0.4;
    var gridSizeX=200,gridSizeY=200,gridStep=10;
    var ctxHeight, ctxWidth;
    var prevX=0, prevY=0;

//    var colorGrid="#bbbbbb", colorLine="#000000";
    var sliderHor, sliderVer;
    var layerNumStore, progressStore={from: 0, to: -1};
    var lastX, lastY;
    var dragStart,dragged;
    var scaleFactor = 1.1;
    var model;
    var initialized=false;
    var displayType = {speed: 1, expermm: 2, volpersec: 3};
    var renderOptions = {
        showMoves: true,
        showRetracts: true,
		showLastPos: false,
        colorGrid: "#bbbbbb",
        extrusionWidth: 1,
//        colorLine: ["#000000", "#aabb88",  "#ffe7a0", "#6e7700", "#331a00", "#44ba97", "#08262f", "#db0e00", "#ff9977"],
        colorLine: ["#000000", "#45c7ba",  "#a9533a", "#ff44cc", "#dd1177", "#eeee22", "#ffbb55", "#ff5511", "#777788", "#ff0000", "#ffff00"],
        colorLineLen: 9,
        colorMove: "#00ff00",
        colorRetract: "#ff0000",
        colorRestart: "#0000ff",
		colorLastPos: "#ff00ff",
        sizeRetractSpot: 2,
        modelCenter: {x: 0, y: 0},
        moveModel: true,
        differentiateColors: true,
		fadeLines: false,
        showNextLayer: false,
        alpha: false,
        actualWidth: false,
        renderErrors: false,
        renderAnalysis: false,
        speedDisplayType: displayType.speed,
        invertAxes: {x: false, y: false},
        bed: {x: 200, y: 200},
        bedOffset: {x: 0, y: 0},
        containerID: "canvas"
    };

    var offsetModelX=0, offsetModelY=0;
    var speeds = [];
    var speedsByLayer = {};
    var volSpeeds = [];
    var volSpeedsByLayer = {};
    var extrusionSpeeds = [];
    var extrusionSpeedsByLayer = {};
    var currentInvertX = false, currentInvertY = false;
    var scaleX = 1, scaleY = 1;

	var toHex = function(n){
	  var hex = n.toString(16);
	  while (hex.length < 2) {hex = "0" + hex; }
	  return hex;
	};

    var reRender = function(){
        var gCodeOpts = GCODE.gCodeReader.getOptions();
        var p1 = ctx.transformedPoint(0,0);
        var p2 = ctx.transformedPoint(canvas.width,canvas.height);
        ctx.clearRect(p1.x,p1.y,p2.x-p1.x,p2.y-p1.y);
        drawGrid();
        if(renderOptions['alpha']){ctx.globalAlpha = 0.6;}
        else {ctx.globalAlpha = 1;}
        if(renderOptions['actualWidth']){renderOptions['extrusionWidth'] = gCodeOpts['filamentDia']*gCodeOpts['wh']/zoomFactor;}
        else {renderOptions['extrusionWidth'] = gCodeOpts['filamentDia']*gCodeOpts['wh']/zoomFactor/2;}
        if(renderOptions['showNextLayer'] && layerNumStore < model.length - 1) {
            drawLayer(layerNumStore+1, 0, GCODE.renderer.getLayerNumSegments(layerNumStore+1), true);
        }
        drawLayer(layerNumStore, progressStore.from, progressStore.to);
    };

    function trackTransforms(ctx){
        var svg = document.createElementNS("http://www.w3.org/2000/svg",'svg');
        var xform = svg.createSVGMatrix();
        ctx.getTransform = function(){ return xform; };

        var savedTransforms = [];
        var save = ctx.save;
        ctx.save = function(){
            savedTransforms.push(xform.translate(0,0));
            return save.call(ctx);
        };
        var restore = ctx.restore;
        ctx.restore = function(){
            xform = savedTransforms.pop();
            return restore.call(ctx);
        };

        var scale = ctx.scale;
        ctx.scale = function(sx,sy){
            xform = xform.scaleNonUniform(sx,sy);
            return scale.call(ctx,sx,sy);
        };
        var rotate = ctx.rotate;
        ctx.rotate = function(radians){
            xform = xform.rotate(radians*180/Math.PI);
            return rotate.call(ctx,radians);
        };
        var translate = ctx.translate;
        ctx.translate = function(dx,dy){
            xform = xform.translate(dx,dy);
            return translate.call(ctx,dx,dy);
        };
        var transform = ctx.transform;
        ctx.transform = function(a,b,c,d,e,f){
            var m2 = svg.createSVGMatrix();
            m2.a=a; m2.b=b; m2.c=c; m2.d=d; m2.e=e; m2.f=f;
            xform = xform.multiply(m2);
            return transform.call(ctx,a,b,c,d,e,f);
        };
        var setTransform = ctx.setTransform;
        ctx.setTransform = function(a,b,c,d,e,f){
            xform.a = a;
            xform.b = b;
            xform.c = c;
            xform.d = d;
            xform.e = e;
            xform.f = f;
            return setTransform.call(ctx,a,b,c,d,e,f);
        };
        var pt  = svg.createSVGPoint();
        ctx.transformedPoint = function(x,y){
            pt.x=x; pt.y=y;
            return pt.matrixTransform(xform.inverse());
        }
    }


    var  startCanvas = function() {
        canvas = document.getElementById(renderOptions["containerID"]);

        
        if (!canvas.getContext) {
            throw "exception";
        }
        ctx = canvas.getContext('2d');
        canvas.style.height = canvas.height + "px";
        canvas.style.width = canvas.width + "px";
        ctxHeight = canvas.height;
        ctxWidth = canvas.width;
        lastX = ctxWidth/2;
        lastY = ctxHeight/2;
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        trackTransforms(ctx);

        // dragging => translating
        canvas.addEventListener('mousedown', function(event){
            document.body.style.mozUserSelect = document.body.style.webkitUserSelect = document.body.style.userSelect = 'none';

            // remember starting point of dragging gesture
            lastX = event.offsetX || (event.pageX - canvas.offsetLeft);
            lastY = event.offsetY || (event.pageY - canvas.offsetTop);
            dragStart = ctx.transformedPoint(lastX, lastY);

            // not yet dragged anything
            dragged = false;
        }, false);

        canvas.addEventListener('mousemove', function(event){
            // save current mouse coordinates
            lastX = event.offsetX || (event.pageX - canvas.offsetLeft);
            lastY = event.offsetY || (event.pageY - canvas.offsetTop);

            // mouse movement => dragged
            dragged = true;

            if (dragStart !== undefined){
                // translate
                var pt = ctx.transformedPoint(lastX,lastY);
                ctx.translate(pt.x - dragStart.x, pt.y - dragStart.y);
                reRender();

                offsetModelX = 0;
                offsetModelY = 0;
                scaleX = 1;
                scaleY = 1;

            }
        }, false);

        canvas.addEventListener('mouseup', function(event){
            // reset dragStart
            dragStart = undefined;
            if (!dragged) zoom(event.shiftKey ? -1 : 1 );
        }, false);

        // mouse wheel => zooming
        var zoom = function(clicks){
            // focus on last mouse position prior to zoom
            var pt = ctx.transformedPoint(lastX, lastY);
            ctx.translate(pt.x,pt.y);

            // determine zooming factor and perform zoom
            var factor = Math.pow(scaleFactor,clicks);
            ctx.scale(factor,factor);

            // return to old position
            ctx.translate(-pt.x,-pt.y);

            // render
            reRender();

            // disable conflicting options
            offsetModelX = 0;
            offsetModelY = 0;
            scaleX = 1;
            scaleY = 1;
        };
        var handleScroll = function(event){
            var delta;

            // determine zoom direction & delta
            if (event.detail < 0 || event.wheelDelta > 0) {
                delta = zoomFactorDelta;
            } else {
                delta = -1 * zoomFactorDelta;
            }
            if (delta) zoom(delta);

            return event.preventDefault() && false;
        };
        canvas.addEventListener('DOMMouseScroll',handleScroll,false);
        canvas.addEventListener('mousewheel',handleScroll,false);
    };

    var drawGrid = function() {
        var x, y;
        var width = renderOptions["bed"]["x"];
        var height = renderOptions["bed"]["y"];

        var minX, maxX, minY, maxY;
        minX = 0 + renderOptions["bedOffset"]["x"];
        maxX = width + renderOptions["bedOffset"]["x"];
        minY = 0 + renderOptions["bedOffset"]["y"];
        maxY = height + renderOptions["bedOffset"]["y"];

        //~ bed outline and origin
        ctx.beginPath();
        ctx.strokeStyle = renderOptions["colorGrid"];
        ctx.fillStyle = "#ffffff";
        ctx.lineWidth = 2;

        // outline
        ctx.rect(minX * zoomFactor, -1 * minY * zoomFactor, width * zoomFactor, -1 * height * zoomFactor);

        // origin
        ctx.moveTo(minX * zoomFactor, 0);
        ctx.lineTo(maxX * zoomFactor, 0);
        ctx.moveTo(0, -1 * minY * zoomFactor);
        ctx.lineTo(0, -1 * maxY * zoomFactor);

        // draw
        ctx.fill();
        ctx.stroke();

        ctx.strokeStyle = renderOptions["colorGrid"];
        ctx.lineWidth = 1;

        //~~ grid starting from origin
        ctx.beginPath();
        for (x = minX; x <= maxX; x += gridStep) {
            ctx.moveTo(x * zoomFactor, -1 * minY * zoomFactor);
            ctx.lineTo(x * zoomFactor, -1 * maxY * zoomFactor);
        }
        ctx.stroke();

        ctx.beginPath();
        for (y = minY; y <= maxY; y += gridStep) {
            ctx.moveTo(minX * zoomFactor, -1 * y * zoomFactor);
            ctx.lineTo(maxX * zoomFactor, -1 * y * zoomFactor);
        }
        ctx.stroke();
    };

    var drawLayer = function(layerNum, fromProgress, toProgress, isNextLayer){
        var i, speedIndex= 0, prevZ = 0;
        isNextLayer = typeof isNextLayer !== 'undefined' ? isNextLayer : false;
        if(!isNextLayer){
            layerNumStore=layerNum;
            progressStore = {from: fromProgress, to: toProgress};
        }
        if(!model||!model[layerNum])return;

        var cmds = model[layerNum];
        var x, y;

//        if(toProgress === -1){
//            toProgress=cmds.length;
//        }

        if(fromProgress>0){
            prevX = cmds[fromProgress-1].x*zoomFactor;
            prevY = -cmds[fromProgress-1].y*zoomFactor;
        }else if(fromProgress===0 && layerNum==0){
            if(model[0]&&typeof(model[0].x) !== 'undefined' && typeof(model[0].y) !== 'undefined'){
                prevX = model[0].x*zoomFactor;
                prevY = -model[0].y*zoomFactor;
            }else {
                prevX = 0;
                prevY = 0;
            }
        }else if(typeof(cmds[0].prevX) !== 'undefined' && typeof(cmds[0].prevY) !== 'undefined'){
            prevX = cmds[0].prevX*zoomFactor;
            prevY = -cmds[0].prevY*zoomFactor;
        }else{
            if(model[layerNum-1]){
                prevX=undefined;
                prevY=undefined;
                for(i=model[layerNum-1].length-1;i>=0;i--){
                    if(typeof(prevX) === 'undefined' && model[layerNum-1][i].x!==undefined)prevX=model[layerNum-1][i].x*zoomFactor;
                    if(typeof(prevY) === 'undefined' && model[layerNum-1][i].y!==undefined)prevY=-model[layerNum-1][i].y*zoomFactor;
                }
                if(typeof(prevX) === 'undefined')prevX=0;
                if(typeof(prevY) === 'undefined')prevY=0;
            }else{
                prevX=0;
                prevY=0;
            }
        }

        prevZ = GCODE.renderer.getZ(layerNum);

//        ctx.strokeStyle = renderOptions["colorLine"];
        for(i=fromProgress;i<=toProgress;i++){
            ctx.lineWidth = 1;

            if(typeof(cmds[i]) === 'undefined')continue;

            if(typeof(cmds[i].prevX) !== 'undefined' && typeof(cmds[i].prevY) !== 'undefined'){
                prevX = cmds[i].prevX*zoomFactor;
                prevY = -cmds[i].prevY*zoomFactor;
            }
//                console.log(cmds[i]);
            if(typeof(cmds[i].x)==='undefined'||isNaN(cmds[i].x))x=prevX/zoomFactor;
            else x = cmds[i].x;
            if(typeof(cmds[i].y) === 'undefined'||isNaN(cmds[i].y))y=prevY/zoomFactor;
            else y = -cmds[i].y;
            if(renderOptions["differentiateColors"]&&!renderOptions['showNextLayer']&&!renderOptions['renderAnalysis']){
//                if(speedsByLayer['extrude'][prevZ]){
                if(renderOptions['speedDisplayType'] === displayType.speed){
                    speedIndex = speeds['extrude'].indexOf(cmds[i].speed);
                }else if(renderOptions['speedDisplayType'] === displayType.expermm){
                    speedIndex = volSpeeds.indexOf(cmds[i].volPerMM);
                }else if(renderOptions['speedDisplayType'] === displayType.volpersec){
                    speedIndex = extrusionSpeeds.indexOf((cmds[i].volPerMM*cmds[i].speed/60).toFixed(3));
                }else{
                    speedIndex=0;
                }
//                    speedIndex = GCODE.ui.ArrayIndexOf(speedsByLayer['extrude'][prevZ], function(obj) {return obj.speed === cmds[i].speed;});
//                } else {
//                    speedIndex = -1;
//                }
                if(speedIndex === -1){
                    speedIndex = 0;
                }else if(speedIndex > renderOptions["colorLineLen"] -1){
                    speedIndex = speedIndex % (renderOptions["colorLineLen"]-1);
    //                console.log("Too much colors");
                }
            }else if(renderOptions['showNextLayer']&&isNextLayer){
                speedIndex=3;
            }else if(renderOptions['renderErrors']){
                if(cmds[i].errType === 2){
                    speedIndex=9;
//                    console.log("l: " + layerNum + " c: " + i);
                }else if(cmds[i].errType === 1){
                    speedIndex=10;
                }else{
                    speedIndex=0;
                }
            }else if(renderOptions['renderAnalysis']){
//                if(cmds[i].errType === 2){
//                    speedIndex=-1;
//                }else{
//                    speedIndex=0;
//                }
                if(layerNum !== 0)speedIndex = -1;
                else speedIndex=0;
            }else{
                speedIndex=0;
            }

            if(!cmds[i].extrude&&!cmds[i].noMove){
//                ctx.stroke();
                if(cmds[i].retract == -1){
                    if(renderOptions["showRetracts"]){

                        ctx.strokeStyle = renderOptions["colorRetract"];
                        ctx.fillStyle = renderOptions["colorRetract"];
                        ctx.beginPath();
                        ctx.arc(prevX, prevY, renderOptions["sizeRetractSpot"], 0, Math.PI*2, true);
                        ctx.stroke();
                        ctx.fill();
                    }
                }
                if(renderOptions["showMoves"]){
                    ctx.strokeStyle = renderOptions["colorMove"];
                    ctx.beginPath();
                    ctx.moveTo(prevX, prevY);
                    ctx.lineTo(x*zoomFactor,y*zoomFactor);
                    ctx.stroke();
                }
//                ctx.strokeStyle = renderOptions["colorLine"][0];
//                ctx.beginPath();
//                console.log("moveto: "+cmds[i].x+":"+cmds[i].y)
//                ctx.moveTo(cmds[i].x*zoomFactor,cmds[i].y*zoomFactor);
            }
            else if(cmds[i].extrude){
                if(cmds[i].retract==0){
                    if(speedIndex>=0){
                        var color = renderOptions["colorLine"][speedIndex];
						if (renderOptions["fadeLines"]) {
							var alpha = 255 - (toProgress-i);
							if ( alpha < 50 ) alpha = 50;
							color = color.substr(0, 7) + toHex(alpha);
						}
						ctx.strokeStyle = color;
                    }else if(speedIndex===-1){
                        var val = parseInt(cmds[i].errLevelB).toString(16);
//                        var val = '8A';
                        var crB = "#" + "00".substr(0,2-val.length) + val + '0000';
                        val = parseInt(cmds[i].errLevelE).toString(16);
                        var crE = "#" + "00".substr(0,2-val.length) + val + '0000';
//                        if(renderOptions['showMoves'])console.log(cr);
                        var gradient = ctx.createLinearGradient(prevX, prevY, x*zoomFactor,y*zoomFactor);
                        if(cmds[i].errType === 1){
                            var limit = (1-cmds[i].errDelimiter);
                            if (limit >= 0.99) limit = 0.99;
                            gradient.addColorStop(0, "#000000");
                            gradient.addColorStop(limit, "#000000");
                            gradient.addColorStop(limit+0.01, crE);
                            gradient.addColorStop(1, crE);
                        }else if(cmds[i].errType === 2){
                            gradient.addColorStop(0, crB);
                            var limit = cmds[i].errDelimiter;
                            if (limit >= 0.99) limit = 0.99;
                            gradient.addColorStop(limit, crB);
                            gradient.addColorStop(limit+0.01, "#000000");
                            gradient.addColorStop(1, "#000000");
                        }else{
                            gradient.addColorStop(0, crB);
                            gradient.addColorStop(1, crE);
                        }
                        ctx.strokeStyle = gradient;
                    }
                    ctx.lineWidth = renderOptions['extrusionWidth'];
                    ctx.beginPath();
                    ctx.moveTo(prevX, prevY);
                    ctx.lineTo(x*zoomFactor,y*zoomFactor);
                    ctx.stroke();
                }else {
                    if(renderOptions["showRetracts"]){
//                        ctx.stroke();
                        ctx.strokeStyle = renderOptions["colorRestart"];
                        ctx.fillStyle = renderOptions["colorRestart"];
                        ctx.beginPath();
                        ctx.arc(prevX, prevY, renderOptions["sizeRetractSpot"], 0, Math.PI*2, true);
                        ctx.stroke();
                        ctx.fill();
//                        ctx.strokeStyle = renderOptions["colorLine"][0];
//                        ctx.beginPath();
                    }
                }
            }
            prevX = x*zoomFactor;
            prevY = y*zoomFactor;
        }

		if(renderOptions["showLastPos"]){
			ctx.strokeStyle = renderOptions["colorLastPos"];
			ctx.fillStyle = renderOptions["colorLastPos"];
			ctx.beginPath();
			ctx.arc(prevX, prevY, renderOptions["sizeRetractSpot"], 0, Math.PI*2, true);
			ctx.stroke();
			ctx.fill();
		}
		
        ctx.stroke();
    };

    var applyOffsets = function() {
        var canvasCenter;

        // determine bed and model offsets
        if (ctx) ctx.translate(-offsetModelX, -offsetModelY);
        if (renderOptions["centerViewport"] || renderOptions["zoomInOnModel"]) {
            canvasCenter = ctx.transformedPoint(canvas.width / 2, canvas.height / 2);
            if (modelInfo) {
                offsetModelX = canvasCenter.x - (modelInfo.boundingBox.minX + modelInfo.boundingBox.maxX) * zoomFactor / 2;
                offsetModelY = canvasCenter.y + (modelInfo.boundingBox.minY + modelInfo.boundingBox.maxY) * zoomFactor / 2;
            } else {
                offsetModelX = 0;
                offsetModelY = 0;
            }
        } else if (modelInfo && renderOptions["moveModel"]) {
            offsetModelX = (renderOptions["bed"]["x"] / 2 - (modelInfo.boundingBox.minX + modelInfo.boundingBox.maxX) / 2) * zoomFactor;
            offsetModelY = -1 * (renderOptions["bed"]["y"] / 2 - (modelInfo.boundingBox.minY + modelInfo.boundingBox.maxY) / 2) * zoomFactor;
        } else {
            offsetModelX = 0;
            offsetModelY = 0;
        }
        if (ctx) ctx.translate(offsetModelX, offsetModelY);
    };

    var applyZoom = function() {
        // get middle of canvas
        var pt = ctx.transformedPoint(canvas.width/2,canvas.height/2);

        // get current transform
        var transform = ctx.getTransform();

        // move to middle of canvas, reset scale, move back
        if (scaleX && scaleY && transform.a && transform.d) {
            ctx.translate(pt.x, pt.y);
            ctx.scale(1 / scaleX, 1 / scaleY);
            ctx.translate(-pt.x, -pt.y);
            transform = ctx.getTransform();
        }

        if (modelInfo && renderOptions["zoomInOnModel"]) {
            // if we need to zoom in on model, scale factor is calculated by longer side of object in relation to that axis of canvas
            var width = modelInfo.boundingBox.maxX - modelInfo.boundingBox.minX;
            var length = modelInfo.boundingBox.maxY - modelInfo.boundingBox.minY;

            var scaleF = width > length ? (canvas.width - 10) / width : (canvas.height - 10) / length;
            scaleF /= zoomFactor;
            if (transform.a && transform.d) {
                scaleX = scaleF / transform.a * (renderOptions["invertAxes"]["x"] ? -1 : 1);
                scaleY = scaleF / transform.d * (renderOptions["invertAxes"]["y"] ? -1 : 1);
                ctx.translate(pt.x,pt.y);
                ctx.scale(scaleX, scaleY);
                ctx.translate(-pt.x, -pt.y);
            }
        } else {
            // reset scale to 1
            scaleX = 1;
            scaleY = 1;
        }
    };


// ***** PUBLIC *******
    return {
        init: function(){
            startCanvas();
            initialized = true;
            var width = renderOptions["bed"]["x"];
            var height = renderOptions["bed"]["y"];
            zoomFactor = Math.min((canvas.width - 10) / width, (canvas.height - 10) / height);

	        var minX, maxX, minY, maxY;
	        minX = (0 + renderOptions["bedOffset"]["x"]) * zoomFactor;
	        maxX = (width + renderOptions["bedOffset"]["x"]) * zoomFactor;
	        minY = (0 + renderOptions["bedOffset"]["y"]) * zoomFactor;
	        maxY = (height + renderOptions["bedOffset"]["y"]) * zoomFactor;

            var translationX, translationY;
            translationX = -minX + 5;
            translationY = maxY +5;
            ctx.translate(translationX, translationY);

            offsetModelX = 0;
            offsetModelY = 0;
            offsetBedX = 0;
            offsetBedY = 0;
        },
        setOption: function(options){
            var mustRefresh = false;
            var dirty = false;
            for (var opt in options) {
                if (!renderOptions.hasOwnProperty(opt) || !options.hasOwnProperty(opt)) continue;
                if (options[opt] === undefined) continue;
                if (renderOptions[opt] == options[opt]) continue;

                dirty = true;
                renderOptions[opt] = options[opt];
                if ($.inArray(opt, ["moveModel", "centerViewport", "zoomInOnModel", "bed", "invertAxes"]) > -1) {
                    mustRefresh = true;
                }
            }

            if (!dirty) return;
            if(initialized) {
                if (mustRefresh) {
                    this.refresh();
                } else {
                    reRender();
                }
            }
        },
        getOptions: function(){
            return renderOptions;
        },
        debugGetModel: function(){
            return model;
        },
        render: function(layerNum, fromProgress, toProgress){
            if (!initialized) this.init();

            var p1 = ctx.transformedPoint(0, 0);
            var p2 = ctx.transformedPoint(canvas.width, canvas.height);
            ctx.clearRect(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y);
            drawGrid();
            if (model && model.length) {
                if (layerNum < model.length) {
                    if (renderOptions['showNextLayer'] && layerNum < model.length - 1) {
                        drawLayer(layerNum + 1, 0, this.getLayerNumSegments(layerNum + 1), true);
                    }
                    if (renderOptions['showPreviousLayer'] && layerNum > 0) {
                        drawLayer(layerNum - 1, 0, this.getLayerNumSegments(layerNum - 1), true);
                    }
                    drawLayer(layerNum, fromProgress, toProgress);
                } else {
                    console.log("Got request to render non-existent layer");
                }
            }
        },
        getModelNumLayers: function(){
            return model ? model.length : 1;
        },
        getLayerNumSegments: function(layer){
            if(model){
                return model[layer]?model[layer].length:1;
            }else{
                return 1;
            }
        },
        clear: function() {
            offsetModelX = 0;
            offsetModelY = 0;
            scaleX = 1;
            scaleY = 1;
            speeds = [];
            speedsByLayer = {};
            modelInfo = undefined;

            this.doRender([], 0);
        },
        doRender: function(mdl, layerNum){
            model = mdl;
            modelInfo = undefined;

            prevX = 0;
            prevY = 0;
            if (!initialized) this.init();

            var toProgress = 1;
            if (model && model.length) {
                modelInfo = GCODE.gCodeReader.getModelInfo();
                speeds = modelInfo.speeds;
                speedsByLayer = modelInfo.speedsByLayer;
                if (model[layerNum]) {
                    toProgress = model[layerNum].length;
                }
            }

            applyOffsets();
            applyZoom();

            this.render(layerNum, 0, toProgress);
        },
        refresh: function(layerNum) {
            if (!layerNum) layerNum = layerNumStore;
            this.doRender(model, layerNum);
        },
        getZ: function(layerNum){
            if(!model || !model[layerNum]){
                return '-1';
            }
            var cmds = model[layerNum];
            for(var i = 0; i < cmds.length; i++){
                if(cmds[i].prevZ !== undefined) return cmds[i].prevZ;
            }
            return '-1';
        }

}
}());

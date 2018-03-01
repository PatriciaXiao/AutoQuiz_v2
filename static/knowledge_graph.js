/* 
 * for echarts documentation:
 * https://ecomfe.github.io/echarts-doc/public/en/index.html
 *
 */
function render_graph(roam) {
    var dom = document.getElementById("graph_container");
    var myChart = echarts.init(dom);
    var app = {};
    option = null;
    option = {
        /*
        title: {
            text: 'Graph sample'
        },
        */
        tooltip: {
            // formatter: '{b} <br> mastery degree estimate: {c} % '
            formatter: function (params, ticket, callback) {
                            // console.log(params)
                            if (params.dataType == 'node') {
                                return params.name + '<br> mastery degree estimate: ' + params.value + '%';
                            }
                        }
        },
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        series : [
            {
                type: 'graph',
                layout: 'none',
                symbolSize: 50,
                roam: roam,
                label: {
                    normal: {
                        show: true
                    }
                },
                edgeSymbol: ['circle', 'arrow'],
                edgeSymbolSize: [4, 10],
                edgeLabel: {
                    normal: {
                        textStyle: {
                            fontSize: 20
                        }
                    }
                },
                data: get_knowledge_graph_data(),
                // links: [],
                links: get_knowledge_graph_link(),
                lineStyle: {
                    normal: {
                        opacity: 0.9,
                        width: 2,
                        curveness: 0
                    }
                }/*,
                itemStyle: {
                    normal: {
                        color: "green",
                    }
                }*/
            }
        ]
    };
    if (option && typeof option === "object") {
        // console.log(option.series[0].data)
        // option.series[0].data.forEach(function (node) {
            //console.log(node.itemStyle)
            //// node.itemStyle = {
            ////         normal: {
            ////             color: "green",
            ////         }
            ////     };
            //console.log(node.itemStyle)
        // })
        myChart.setOption(option, true);
        // only nodes are clickable
        myChart.on('click', function (params) {
            // request_exercise_section(0);
            // console.log(params);
            if(params.dataType=="node") {
                var node_name = params.data.name;
                // request_exercise_section(params.data.name);
                request_topic_id(params.data.id, 0)
            }
        })
    }
}
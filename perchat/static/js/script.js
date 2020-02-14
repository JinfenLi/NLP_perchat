$(document).ready(function () {

    var popupLoading = '<i class="notched circle loading icon green"></i> Loading...';
    var message_count = 0;
    var ENTER_KEY = 13;

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });

    function scrollToBottom() {

        var $messages = $('.messages');

        if ($messages.length>0){
            $('#message-textarea').focus();

            $messages.scrollTop($messages[0].scrollHeight);
        }


    }

    var page = 1;

    function load_messages() {
        var $messages = $('.messages');
        var position = $messages.scrollTop();
        if (position === 0 && socket.nsp !== '/anonymous'&& socket.nsp !== '/privatechat'&& socket.nsp !== '/chat') {
            page++;
            $('.ui.loader').toggleClass('active');
            $.ajax({
                url: messages_url,
                type: 'GET',
                data: {page: page},
                success: function (data) {
                    var before_height = $messages[0].scrollHeight;
                    $(data).prependTo(".messages").hide().fadeIn(800);
                    var after_height = $messages[0].scrollHeight;
                    flask_moment_render_all();
                    $messages.scrollTop(after_height - before_height);
                    $('.ui.loader').toggleClass('active');
                    activateSemantics();
                },
                error: function () {
                    alert('No more messages.');
                    $('.ui.loader').toggleClass('active');
                }
            });
        }
    }

    $('.messages').scroll(load_messages);
    if (typeof socket!=="undefined"){
        socket.on('user count', function (data) {
        $('#user-count').html(data.count);
    });
    }

    if (typeof socket!=="undefined"){
        socket.on('new message', function (data) {

        message_count++;
        if (!document.hasFocus()) {
            document.title = '(' + message_count + ') ' + 'Unread';
        }
        if (data.user_id !== current_user_id) {
            messageNotify(data);
        }
        // alert(data.nickname);
        $('.messages').append(data.message_html);
        flask_moment_render_all();
        scrollToBottom();
        activateSemantics();
    });
    }

    if (typeof socket!=="undefined"){
        socket.on('check', function (data) {
        var quote = $('#quote').text();
        var $textarea = $('#message-textarea');

        if (data.user_id === current_user_id) {


            if (data.result) {

                socket.emit('new message', quote+data.message_body, 1,room_id);
                $textarea.val('');
                $("#quote").text('');
                $('#deletequote').hide();
            }
            else {

                if (confirm("your message is not persuasive, are you sure to send it?")) {
                    socket.emit('new message', quote+data.message_body, 0,room_id);
                    $textarea.val('');
                    $("#quote").text('');
                    $('#deletequote').hide();


                }
            }
        }

                    });
    }


    function new_message(e) {
        var $textarea = $('#message-textarea');
        var message_body = $textarea.val().trim();




        if (e.which === ENTER_KEY && !e.shiftKey && message_body) {
            e.preventDefault();
            socket.emit('check', message_body,room_id);

                // socket.emit('new message', message_body);
                // $textarea.val('')

        }
    }

    // submit message
    $('#message-textarea').on('keydown', new_message.bind(this));



    // submit snippet
    $('#snippet-button').on('click', function () {
        var $snippet_textarea = $('#snippet-textarea');
        var message = $snippet_textarea.val();
        if (message.trim() !== '') {
            socket.emit('new message', message);
            $snippet_textarea.val('')
        }
    });

    // open message modal on mobile
    $("#mobile-message-textarea").focus(function () {
        if (screen.width < 600) {
            $('#mobile-new-message-modal').modal('show');
            $('#mobile-message-textarea').focus()
        }
    });

    $('#send-button').on('click', function () {
        var $mobile_textarea = $('#mobile-message-textarea');
        // var quote = $('#quote');
        var message = $mobile_textarea.val();
        if (message.trim() !== '') {
            socket.emit('new message', message);
            $mobile_textarea.val('')
        }
    });

    // quote message
    $('body').delegate('.quote-button','click', function () {
        // $('#quote').show();
        $('#deletequote').show();

        var $textarea = $('#message-textarea');
        var message = $(this).parent().parent().parent().find('.message-body').text();
        var name = $(this).parent().parent().parent().find('.nickname').text();
        $("#quote").text('>' + name+': '+message+ '\n\n');
        // $textarea.val('> ' + name+'\n'+message + '\n\n');
        $textarea.val($textarea.val()).focus()

    });
    $('#deletequote').click(function () {

                $('#quote').text('');
                $('#deletequote').hide();



            });

    function messageNotify(data) {
        if (Notification.permission !== "granted")
            Notification.requestPermission();
        else {
            var notification = new Notification("Message from " + data.nickname, {
                icon: data.gravatar,
                body: data.message_body.replace(/(<([^>]+)>)/ig, "")
            });

            notification.onclick = function () {
                window.open(root_url);
            };
            setTimeout(function () {
                notification.close()
            }, 4000);
        }
    }

    function activateSemantics() {
        $('.ui.dropdown').dropdown();
        $('.ui.checkbox').checkbox();

        $('.message .close').on('click', function () {
            $(this).closest('.message').transition('fade');
        });

        $('#toggle-sidebar').on('click', function () {
            $('.menu.sidebar').sidebar('setting', 'transition', 'overlay').sidebar('toggle');
        });

        $('#show-help-modal').on('click', function () {
            $('.ui.modal.help').modal({blurring: true}).modal('show');
        });

        $('#show-snippet-modal').on('click', function () {
            $('.ui.modal.snippet').modal({blurring: true}).modal('show');



        });

        $('.pop-card').popup({
            inline: true,
            on: 'hover',
            hoverable: true,
            html: popupLoading,
            delay: {
                show: 200,
                hide: 200
            },
            onShow: function () {
                var popup = this;
                popup.html(popupLoading);
                $.get({
                    url: $(popup).prev().data('href')
                }).done(function (data) {
                    popup.html(data);
                }).fail(function () {
                    popup.html('Failed to load profile.');
                });
            }
        });
    }

    function init() {
        // desktop notification
        document.addEventListener('DOMContentLoaded', function () {
            if (!Notification) {
                alert('Desktop notifications not available in your browser.');
                return;
            }

            if (Notification.permission !== "granted")
                Notification.requestPermission();
        });

        $(window).focus(function () {
            message_count = 0;
            document.title = 'perchat';
        });

        activateSemantics();
        scrollToBottom();
    }

    // delete message
    $('body').delegate('.delete-button','click', function () {
        var $this = $(this);
        $.ajax({
            type: 'DELETE',
            url: $this.data('href'),
            success: function () {
                $this.parent().parent().parent().remove();
            },
            error: function () {
                alert('Oops, something was wrong!')
            }
        });
    });

    // delete user
    $(document).on('click', '.delete-user-button', function () {
        var $this = $(this);
        $.ajax({
            type: 'DELETE',
            url: $this.data('href'),
            success: function () {
                alert('Success, this user is gone!')
            },
            error: function () {
                alert('Oops, something was wrong!')
            }
        });
    });

    $('#joinroomtable').on('click', ":button",function () {

    index = $(this).closest("tr").find("td").eq(0).text();
    $(this).parents("tr").remove();




    $.ajax({
    url: "/joinroom",
    type:"post",
    data: {'name': index},
    success: function(response, textStatus, fn) {
      // document.getElementById("feedbackfeedback").innerHTML=data;
      // $("#progressBar").attr('hidden', 'true');
      // $("#compareSubmit").removeAttr('hidden');
      // if (response['error'] != "") {
      //   $("#errorMessage").text(response['error']);
      //   $("#errorMessage").removeAttr('hidden');
        var data = response['data'];
            var tr = "<tr>"+
                "<td>"+data.name+ "</td>"+
                "<td>"+data.description+"</td>" +
                "<td>"+data.time+"</td>"+
                "<td>"+data.owner+"</td>"+
                "<td>1</td>" +
                "<td>wait</td>"+
                "</tr>";
            if("#userwaitroom:waitnoroom".length>0){
                $("#waitnoroom").remove();
            }
			$("#userwaitroom").append(tr);
			alert(response['message']);
        $('#joinroommodal').modal('hide');


      },
      error: function () {
                alert('Oops, something was wrong!')
            }
    });
  });

    $('#createroom').on('click',function () {

        var name =$("#room-name").val();
        var description = $("#room-description").val();
        var data= {
                    data: JSON.stringify({
                        'name': name,"description":description
                    })
                };

        $.ajax({
        url: "createroom",
        type:"post",
        data: data,
        success: function(response, textStatus, fn) {
          // document.getElementById("feedbackfeedback").innerHTML=data;
          // $("#progressBar").attr('hidden', 'true');
          // $("#compareSubmit").removeAttr('hidden');


          if (response['result']) {

            // alert(response['message']);

            $('#createroommodal').modal('hide');
            var data = response['data'];
            var tr = "<tr>"+
                "<td>"+data.name+ "</td>"+
                "<td>"+data.description+"</td>" +
                "<td>"+data.time+"</td>"+
                "<td>1</td>" +
                "<td><div class=\"item delete-room-button\"" +
                "                         data-href="+data.deleteurl+"><i class=\"delete icon\"></i></div></td>" +
                "<td><a class=\"btn btn-success\" href="+data.startchaturl+"></a></td>"+
                "</tr>";
            if("#checkroomtable:createnoroom".length>0){
                            $("#createnoroom").remove();
                        }
			$("#checkroomtable").append(tr);


          }
            else{
                alert(response['message'])
            }
        },
          error: function () {
                    alert('Oops, something was wrong!')
                }
        });
      });

    $('#checkroomtable').on('click','.delete-room-button', function () {

        var $this = $(this);
        if (confirm('Are you sure?')){
            $(this).parents("tr").remove();
            $.ajax({
            type: 'DELETE',
            url: $this.data('href'),
            success: function () {


            },
            error: function () {
                alert('Oops, something was wrong!')
            }
        });
        }



    });


    // $('#approve').on('click',function () {
    $('#approvetable').on('click','.control-approve', function () {
        var status = $('input:radio[name="category"]:checked').val();
        var email =$(this).closest("tr").find("td").eq(1).text();
        var roomname = $(this).closest("tr").find("td").eq(2).text();
        $(this).parents("tr").remove();
        $.ajax({
        url: "/validate",
        type:"post",
        data: {'email':email,'roomname':roomname,'status':status},
        success: function(response, textStatus, fn) {

          // $("#progressBar").attr('hidden', 'true');
          // $("#compareSubmit").removeAttr('hidden');

        },
          error: function () {
                    alert('Oops, something was wrong!')
                }
        });
      });

    // $('#deny').on('click',function () {
    $('#approvetable').on('click','.control-deny', function () {
        var status = $('input:radio[name="category"]:checked').val();
        var email =$(this).closest("tr").find("td").eq(1).text();
        var roomname = $(this).closest("tr").find("td").eq(2).text();
        $(this).parents("tr").remove();
        $.ajax({
        url: "/validate",
        type:"post",
        data: {'email':email,'roomname':roomname,'status':status},

        success: function(response, textStatus, fn) {


        },
          error: function () {
                    alert('Oops, something was wrong!')
                }
        });
      });

    if (typeof socket!=="undefined" && (socket.nsp === '/privatechat' || socket.nsp === '/chat')){
        socket.on('connect', function() {
            $('#message-textarea').focus();
            if (room_id.length>0){
                socket.emit('joined', room_id);

            }});
    }




    init();


});

function leave_group_room() {
                socket.emit('left', room_id, function() {
                    socket.disconnect();

                    // go back to the login page
                    window.location.href = home_url;
                });
            }


function leave_private_room() {
                socket.emit('left', room_id, function() {
                    socket.disconnect();

                    // go back to the login page
                    window.location.href = user_url;
                });
            }
